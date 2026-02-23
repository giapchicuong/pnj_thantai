#!/usr/bin/env python3
"""
Tool automation PNJ Thần Tài - Tích Lộc
Luồng: Chưa mua hàng -> Nhập SĐT + Captcha -> Tích Lộc Ngay -> Quay 3 lượt -> Về trang chủ -> Lặp lại
Hỗ trợ chạy nhiều luồng song song: python main.py --workers 10
"""
import argparse
import os
import threading
import time
import base64
from multiprocessing import Process
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchWindowException, NoSuchDriverException
from selenium.webdriver.chrome.service import Service

from http.client import RemoteDisconnected
from urllib3.exceptions import ProtocolError as Urllib3ProtocolError
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from config import (
    BASE_URL,
    BASE_ORIGIN,
    SELECTORS,
    CHECKBOX_TERMS,
    LOADING_SPIN,
    LOADING_TICH_LOC_NGAY,
    CLOUDFLARE_TURNSTILE,
    POPUP_CON_LOOT,
    POPUP_HET_LOOT,
    TIMEOUT_PAGE_LOAD,
    WAIT_AFTER_CLICK,
    IMPLICIT_WAIT,
    WAIT_AFTER_SPIN,
    WAIT_FOR_POPUP_MAX,
    WAIT_FOR_NEXT_SPIN,
    CAPTCHA_API_KEY,
    CAPTCHA_USE_DDDDOCR,
    USE_MANUAL_FALLBACK,
    NUM_WORKERS,
    LOW_MEMORY_MODE,
    MAX_RETRY_PER_PHONE,
    USE_UNDETECTED,
    SUMMARY_INTERVAL,
)
from captcha_solver import solve_captcha_from_bytes


def find_element(driver, selectors: list, by_xpath_markers: tuple = ("//", "[", ".", "#")) -> Optional[object]:
    """Tìm element từ danh sách selectors, trả về element đầu tiên tìm thấy."""
    for sel in selectors:
        try:
            if sel.strip().startswith("//"):
                el = driver.find_element(By.XPATH, sel)
            else:
                el = driver.find_element(By.CSS_SELECTOR, sel)
            if el and el.is_displayed():
                return el
        except Exception:
            continue
    return None


def _hide_video_overlay(driver) -> None:
    """Ẩn video fullscreen chặn click."""
    try:
        driver.execute_script("""
            document.querySelectorAll('video').forEach(v => {
                if (v.style.position === 'fixed' || (v.getAttribute('style') || '').includes('fixed')) {
                    v.style.cssText = 'display:none !important';
                }
            });
        """)
    except Exception:
        pass


def click_element(driver, selectors: list) -> bool:
    """Tìm và click element, trả về True nếu thành công."""
    el = find_element(driver, selectors)
    if el:
        try:
            el.click()
            time.sleep(WAIT_AFTER_CLICK)
            return True
        except Exception as e:
            if "click intercepted" in str(e).lower() or "video" in str(e).lower():
                _hide_video_overlay(driver)
                time.sleep(0.3)
            try:
                driver.execute_script("arguments[0].click();", el)
                time.sleep(WAIT_AFTER_CLICK)
                return True
            except Exception:
                return False
    return False


def get_so_luot_con_lai(driver) -> Optional[int]:
    """Lấy số lượt chơi còn lại (#spSoLuotChoiConLai). Return None nếu không tìm thấy."""
    el = find_element(driver, SELECTORS.get("so_luot_con_lai", []))
    if el:
        try:
            return int(el.text.strip())
        except (ValueError, TypeError):
            pass
    return None


def _wait_loading_hide(driver, selector: str, timeout: float = 10) -> bool:
    """Chờ element loading ẩn (display:none)."""
    step = 0.3
    elapsed = 0.0
    while elapsed < timeout:
        try:
            el = driver.find_element(By.CSS_SELECTOR, selector)
            if not el.is_displayed():
                return True
        except Exception:
            return True
        time.sleep(step)
        elapsed += step
    return False


def _wait_for_spin_popup(driver, timeout: float = WAIT_FOR_POPUP_MAX) -> bool:
    """Đợi popup kết quả quay (ConLuot hoặc HetLuot hiện)."""
    step = 0.3
    elapsed = 0.0
    while elapsed < timeout:
        _hide_video_overlay(driver)
        try:
            for sel in [POPUP_CON_LOOT, POPUP_HET_LOOT]:
                el = driver.find_element(By.CSS_SELECTOR, sel)
                if el.is_displayed():
                    return True
        except Exception:
            pass
        if find_element(driver, SELECTORS["tich_them_loc"]) or find_element(driver, SELECTORS["ve_trang_chu"]):
            return True
        time.sleep(step)
        elapsed += step
    return False


def _wait_for_spin_button(driver, timeout: float = WAIT_FOR_NEXT_SPIN) -> bool:
    """Đợi nút quay xuất hiện (chờ loading ẩn trước)."""
    step = 0.3
    elapsed = 0.0
    while elapsed < timeout:
        _hide_video_overlay(driver)
        _wait_loading_hide(driver, LOADING_SPIN, timeout=2)
        if find_element(driver, SELECTORS["tich_loc_1_luot"]) or find_element(driver, SELECTORS["tich_them_loc"]):
            return True
        time.sleep(step)
        elapsed += step
    return False


def fill_input(driver, selectors: list, value: str) -> bool:
    """Tìm ô input và điền giá trị."""
    el = find_element(driver, selectors)
    if el:
        try:
            el.clear()
            el.send_keys(value)
            time.sleep(0.2)
            return True
        except Exception as e:
            err_s = str(e)
            # Re-raise connection/timeout để worker tạo lại driver
            if "Read timed out" in err_s or "Connection" in err_s or "timed out" in err_s.lower():
                raise
            print(f"[!] Không điền được: {e}")
    return False


def get_captcha_image_bytes(driver) -> Optional[bytes]:
    """Lấy ảnh captcha (base64, URL relative /images/captcha/xxx.jpg)."""
    import requests
    for sel in SELECTORS["captcha_image"]:
        try:
            by = By.XPATH if sel.strip().startswith("//") else By.CSS_SELECTOR
            el = WebDriverWait(driver, 6).until(EC.presence_of_element_located((by, sel)))
            if not el or not el.is_displayed():
                continue
            time.sleep(0.3)
            src = el.get_attribute("src")
            if src and "base64," in src:
                b64 = src.split("base64,")[-1]
                return base64.b64decode(b64)
            if src:
                url = src if src.startswith("http") else urljoin(BASE_ORIGIN + "/", src)
                r = requests.get(url, timeout=10)
                if r.ok:
                    return r.content
            return el.screenshot_as_png
        except Exception:
            continue
    return None


def solve_and_fill_captcha(driver, max_retries: int = 3) -> bool:
    """Lấy captcha, giải bằng Tesseract, điền vào ô. Thử refresh nếu sai."""
    for attempt in range(max_retries):
        img_bytes = get_captcha_image_bytes(driver)
        if not img_bytes:
            print("[Captcha] Không lấy được ảnh.")
            if attempt < max_retries - 1 and click_element(driver, SELECTORS.get("captcha_refresh", [])):
                time.sleep(1)
            continue

        text = solve_captcha_from_bytes(
            img_bytes,
            api_key=CAPTCHA_API_KEY or None,
            use_ddddocr=CAPTCHA_USE_DDDDOCR,
        )
        if not text:
            print("[Captcha] OCR không nhận ra text.")
            if attempt < max_retries - 1 and click_element(driver, SELECTORS.get("captcha_refresh", [])):
                time.sleep(1)
            continue

        print(f"[Captcha] Nhận dạng: {text}")
        if fill_input(driver, SELECTORS["captcha_input"], text):
            return True

        if attempt < max_retries - 1 and click_element(driver, SELECTORS.get("captcha_refresh", [])):
            time.sleep(1)

    return False


def check_and_click_terms(driver) -> None:
    """Tick checkbox đồng ý điều khoản nếu có."""
    for sel in CHECKBOX_TERMS:
        try:
            if sel.startswith("//"):
                el = driver.find_element(By.XPATH, sel)
            else:
                el = driver.find_element(By.CSS_SELECTOR, sel)
            if el and el.is_displayed() and not el.is_selected():
                el.click()
                time.sleep(0.5)
                break
        except Exception:
            continue


def _wait_for_chua_mua_hang(driver, timeout: float = 12) -> bool:
    """Đợi nút Chưa mua hàng xuất hiện (ẩn video trước)."""
    step = 0.5
    elapsed = 0.0
    while elapsed < timeout:
        _hide_video_overlay(driver)
        if find_element(driver, SELECTORS["chua_mua_hang"]):
            return True
        time.sleep(step)
        elapsed += step
    return False


def process_one_phone(driver, phone: str, worker_id: int = 0) -> bool:
    """Xử lý 1 số điện thoại: nhập SĐT, captcha, quay 3 lượt."""
    prefix = f"[W{worker_id}]" if worker_id else ""
    print(f"\n{prefix} [*] Đang xử lý: {phone}")

    # 0. Ẩn video overlay, đợi nút Chưa mua hàng
    _hide_video_overlay(driver)
    if not _wait_for_chua_mua_hang(driver):
        return False

    # 1. Click Chưa mua hàng
    if not click_element(driver, SELECTORS["chua_mua_hang"]):
        print(f"{prefix} [!] Không tìm thấy nút Chưa mua hàng.")
        return False

    time.sleep(1)

    # 2. Tick điều khoản (nếu có)
    check_and_click_terms(driver)

    # 3. Đợi ô nhập SĐT xuất hiện rồi điền (form có thể load chậm)
    for _ in range(24):
        if find_element(driver, SELECTORS["phone_input"]):
            break
        time.sleep(0.5)
    if not fill_input(driver, SELECTORS["phone_input"], phone):
        print(f"{prefix} [!] Không tìm thấy ô nhập SĐT.")
        return False

    # 4. Giải captcha, bấm Tích Lộc Ngay, thử lại nếu sai (popup "Captcha không hợp lệ")
    captcha_ok = False
    for _ in range(5):
        if not solve_and_fill_captcha(driver):
            print(f"{prefix} [!] Không giải được captcha.")
            return False

        if not click_element(driver, SELECTORS["tich_loc_ngay"]):
            print(f"{prefix} [!] Không tìm thấy nút Tích Lộc Ngay.")
            return False

        time.sleep(1)

        if find_element(driver, SELECTORS.get("popup_close", [])):
            print(f"{prefix}     Captcha sai, đóng popup và thử lại...")
            click_element(driver, SELECTORS["popup_close"])
            time.sleep(0.5)
            click_element(driver, SELECTORS.get("captcha_refresh", []))
            time.sleep(0.5)
            fill_input(driver, SELECTORS["captcha_input"], "")
            continue

        captcha_ok = True
        break

    if not captcha_ok and USE_MANUAL_FALLBACK:
        img_bytes = get_captcha_image_bytes(driver)
        if img_bytes:
            debug_path = Path(__file__).parent / "captcha_debug.png"
            Path(debug_path).write_bytes(img_bytes)
            print(f"\n    Đã lưu ảnh captcha vào: {debug_path}")
            manual = input("    Nhập captcha (xem ảnh trên): ").strip()
            if manual:
                fill_input(driver, SELECTORS["captcha_input"], manual)
                click_element(driver, SELECTORS["tich_loc_ngay"])
                time.sleep(2)
                if not find_element(driver, SELECTORS.get("popup_close", [])):
                    captcha_ok = True
                    print("    Nhập tay thành công!")
                else:
                    click_element(driver, SELECTORS["popup_close"])

    if not captcha_ok:
        print(f"{prefix} [!] Captcha sai quá nhiều lần.")
        return False

    time.sleep(0.5)
    _hide_video_overlay(driver)

    # 5b. Nếu đã 0 lượt (SĐT đã chơi hết) -> Về trang chủ, chuyển sang số mới
    remaining = get_so_luot_con_lai(driver)
    if remaining is not None and remaining == 0:
        print(f"{prefix}     SĐT đã hết lượt (0) -> chuyển số mới.")
        click_element(driver, SELECTORS["ve_trang_chu"])
        time.sleep(2)
        return True

    # 6. Quay 3 lượt - chờ loading ẩn -> bấm quay -> chờ popup -> bấm Tích thêm lộc / Về trang chủ
    for turn in range(3):
        if not _wait_for_spin_button(driver):
            print(f"{prefix} [!] Không thấy nút quay lượt {turn + 1} sau {WAIT_FOR_NEXT_SPIN}s.")
        spin_clicked = click_element(driver, SELECTORS["tich_loc_1_luot"])
        if not spin_clicked:
            spin_clicked = click_element(driver, SELECTORS["tich_them_loc"])
        if not spin_clicked:
            print(f"{prefix} [!] Không bấm được nút quay lượt {turn + 1}.")
        else:
            print(f"{prefix}     Quay lượt {turn + 1}/3...")
            _wait_loading_hide(driver, LOADING_SPIN, timeout=WAIT_FOR_POPUP_MAX)
            _wait_for_spin_popup(driver)
            time.sleep(0.3)
            _hide_video_overlay(driver)
            if turn < 2:
                click_element(driver, SELECTORS["tich_them_loc"])
                time.sleep(2.5)
            else:
                # Lượt 3 xong: bấm Về trang chủ ngay trên popup
                click_element(driver, SELECTORS["ve_trang_chu"])
                time.sleep(1)
                print(f"{prefix}     Hoàn thành {phone}.")
                return True

    # 7. Nếu chưa bấm Về trang chủ (lỡ lượt 3 không click được)
    remaining = get_so_luot_con_lai(driver)
    if remaining is not None and remaining > 0:
        print(f"{prefix} [!] Còn {remaining} lượt chưa quay -> retry SĐT.")
        return False

    _hide_video_overlay(driver)
    click_element(driver, SELECTORS["ve_trang_chu"])
    time.sleep(2)
    return True


def load_phones(path: str = "phones.txt", exclude_done_path: str = "completed.txt") -> list[str]:
    """Đọc danh sách SĐT từ file, loại trừ số đã chạy xong (completed.txt) - tránh chạy lại khi restart."""
    p = Path(path)
    if not p.exists():
        return []
    lines = p.read_text(encoding="utf-8").strip().splitlines()
    phones = [line.strip() for line in lines if line.strip() and not line.strip().startswith("#")]
    done = set()
    ep = Path(exclude_done_path)
    if ep.exists():
        done = set(l.strip() for l in ep.read_text(encoding="utf-8").splitlines() if l.strip())
    if done:
        before = len(phones)
        phones = [ph for ph in phones if ph not in done]
        print(f"[*] Đã bỏ qua {before - len(phones)} số đã hoàn thành (resume từ completed.txt)")
    return phones


def _create_driver(headless: bool = False):
    """Tạo Chrome driver - dùng undetected-chromedriver khi USE_UNDETECTED để né Cloudflare."""
    if USE_UNDETECTED:
        import undetected_chromedriver as uc
        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-software-rasterizer")
        if LOW_MEMORY_MODE or headless:
            options.add_argument("--headless=new")
        kwargs = {"options": options, "version_main": 145}
        if os.path.isfile("/usr/bin/google-chrome"):
            kwargs["browser_executable_path"] = "/usr/bin/google-chrome"
        driver = uc.Chrome(**kwargs)
    else:
        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-gpu")
        use_low_mem = LOW_MEMORY_MODE or headless
        if use_low_mem:
            options.add_argument("--headless=new")
            options.add_argument("--disable-background-networking")
            options.add_argument("--disable-default-apps")
            options.add_argument("--disable-sync")
            options.add_argument("--disable-translate")
            options.add_argument("--no-first-run")
            options.add_argument("--disable-software-rasterizer")
            options.add_argument("--disable-features=TranslateUI")
            options.add_argument("--js-flags=--max-old-space-size=256")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
    driver.implicitly_wait(IMPLICIT_WAIT)
    driver.set_page_load_timeout(TIMEOUT_PAGE_LOAD)
    return driver


def _log_cloudflare_status(driver, worker_id: int, timeout: float = 15) -> bool:
    """Chờ element trang PNJ xuất hiện, log trạng thái Cloudflare. Trả về True nếu đã vượt."""
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#btChuaMuaHang, #txtSoDienThoai"))
        )
        print(f"[W{worker_id}] [Cloudflare] Đã vượt Cloudflare ✓")
        return True
    except TimeoutException:
        try:
            driver.find_element(By.CSS_SELECTOR, CLOUDFLARE_TURNSTILE)
            print(f"[W{worker_id}] [Cloudflare] Vẫn đang chờ Turnstile...")
        except Exception:
            try:
                driver.find_element(By.CSS_SELECTOR, "#challenge-running, #cf-challenge-running")
                print(f"[W{worker_id}] [Cloudflare] Vẫn đang chờ challenge...")
            except Exception:
                print(f"[W{worker_id}] [Cloudflare] Chưa thấy nội dung trang (timeout {timeout}s)")
        return False


def _safe_get_url(driver, url: str, max_retries: int = 5) -> bool:
    """Load trang, retry khi timeout, window closed hoặc connection error. Trả về True nếu thành công."""
    for attempt in range(max_retries):
        try:
            driver.get(url)
            return True
        except (TimeoutException, NoSuchWindowException):
            if attempt < max_retries - 1:
                time.sleep(2)
            else:
                raise
        except (Urllib3ProtocolError, RemoteDisconnected):
            if attempt < max_retries - 1:
                time.sleep(6)
            else:
                raise
    return False


def run_worker(
    worker_id: int,
    phones: list[str],
    headless: bool = False,
    stagger_sec: float = 0,
    completed_counter=None,
    not_completed_path: str = "not_completed.txt",
    not_completed_lock=None,
    completed_path: str = "completed.txt",
    completed_lock=None,
):
    try:
        _run_worker_impl(worker_id, phones, headless, stagger_sec,
                        completed_counter, not_completed_path, not_completed_lock,
                        completed_path, completed_lock)
    except (Urllib3ProtocolError, RemoteDisconnected) as e:
        print(f"[W{worker_id}] [!] Chrome connection lỗi, thoát: {e}")
    except Exception as e:
        err_s = str(e)
        if ("Connection aborted" in err_s or "RemoteDisconnected" in err_s or "ProtocolError" in err_s
                or "connection error" in err_s.lower()):
            print(f"[W{worker_id}] [!] Chrome connection lỗi, thoát: {e}")
        else:
            raise


def _run_worker_impl(
    worker_id: int,
    phones: list[str],
    headless: bool = False,
    stagger_sec: float = 0,
    completed_counter=None,
    not_completed_path: str = "not_completed.txt",
    not_completed_lock=None,
    completed_path: str = "completed.txt",
    completed_lock=None,
):
    if stagger_sec > 0:
        time.sleep(stagger_sec)
    time.sleep(3)  # Đợi Chrome cũ (nếu có) thoát hẳn trước khi tạo mới

    driver = None
    max_init_retries = 12
    for attempt in range(max_init_retries):
        try:
            driver = _create_driver(headless=headless)
            if USE_UNDETECTED:
                time.sleep(3)  # Cho Chrome ổn định trước khi load trang
            _safe_get_url(driver, BASE_URL)
            break
        except (TimeoutException, NoSuchWindowException) as e:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass
                driver = None
            if attempt < max_init_retries - 1:
                print(f"[W{worker_id}] [!] Cửa sổ đóng sớm, thử lại ({attempt + 1}/{max_init_retries})...")
                time.sleep(8)
                continue
            raise
        except (Urllib3ProtocolError, RemoteDisconnected) as e:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass
                driver = None
            if attempt < max_init_retries - 1:
                print(f"[W{worker_id}] [!] Chrome connection lỗi, thử lại ({attempt + 1}/{max_init_retries})...")
                time.sleep(15)
                continue
            raise RuntimeError("Không tạo được Chrome driver sau nhiều lần thử (connection error).") from e
        except Exception as e:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass
                driver = None
            err_str = str(e)
            is_retryable_init = (
                "Unable to obtain" in err_str or "not a valid file" in err_str
                or "unexpectedly exited" in err_str or "Can not connect to the Service" in err_str
                or "No such file" in err_str or "Remote end closed connection" in err_str
                or "Connection aborted" in err_str or "RemoteDisconnected" in err_str
                or "ProtocolError" in err_str or isinstance(e, FileNotFoundError)
            )
            if attempt < max_init_retries - 1 and is_retryable_init:
                print(f"[W{worker_id}] [!] Driver lỗi, thử lại ({attempt + 1}/{max_init_retries})...")
                time.sleep(8)
                continue
            raise
    else:
        raise RuntimeError("Không tạo được Chrome driver sau nhiều lần thử.")

    try:
        time.sleep(2)
        _hide_video_overlay(driver)
        _log_cloudflare_status(driver, worker_id)

        i = 0
        total = len(phones)
        while i < total:
            phone = phones[i]
            retry_count = 0

            while retry_count <= MAX_RETRY_PER_PHONE:
                try:
                    _safe_get_url(driver, BASE_URL)
                    time.sleep(4)  # Đợi trang + video render xong (nhiều luồng cần lâu hơn)
                    _hide_video_overlay(driver)

                    ok = process_one_phone(driver, phone, worker_id=worker_id)
                    if ok:
                        if completed_counter is not None:
                            completed_counter.value += 1
                        if completed_path and completed_lock is not None:
                            with completed_lock:
                                Path(completed_path).open("a", encoding="utf-8").write(phone + "\n")
                        elif completed_path:
                            Path(completed_path).open("a", encoding="utf-8").write(phone + "\n")
                        i += 1
                        break
                    retry_count += 1
                    if retry_count <= MAX_RETRY_PER_PHONE:
                        print(f"[W{worker_id}]     Retry {retry_count}/{MAX_RETRY_PER_PHONE}...")
                        time.sleep(2)
                        continue
                    if not_completed_path and not_completed_lock is not None:
                        with not_completed_lock:
                            Path(not_completed_path).open("a", encoding="utf-8").write(phone + "\n")
                    print(f"[W{worker_id}] [!] Bỏ qua {phone} sau {MAX_RETRY_PER_PHONE} lần thất bại.")
                    i += 1
                    break
                except (Urllib3ProtocolError, RemoteDisconnected) as e:
                    print(f"[W{worker_id}] [!] Chrome connection lỗi ({type(e).__name__}), tạo lại driver...")
                    new_driver = None
                    for recreate_attempt in range(3):
                        try:
                            if driver:
                                try:
                                    driver.quit()
                                except Exception:
                                    pass
                                driver = None
                            new_driver = _create_driver(headless=headless)
                            if USE_UNDETECTED:
                                time.sleep(3)
                            _safe_get_url(new_driver, BASE_URL)
                            time.sleep(2)
                            _hide_video_overlay(new_driver)
                            _log_cloudflare_status(new_driver, worker_id)
                            driver = new_driver
                            retry_count += 1
                            if retry_count <= MAX_RETRY_PER_PHONE:
                                time.sleep(2)
                            break
                        except Exception as init_err:
                            print(f"[W{worker_id}] [!] Không tạo lại được driver ({recreate_attempt + 1}/3): {init_err}")
                            if recreate_attempt < 2:
                                time.sleep(12)
                    if driver is None:
                        retry_count = MAX_RETRY_PER_PHONE + 1
                    if retry_count > MAX_RETRY_PER_PHONE:
                        if not_completed_path and not_completed_lock is not None:
                            with not_completed_lock:
                                Path(not_completed_path).open("a", encoding="utf-8").write(phone + "\n")
                        i += 1
                        break
                except (TimeoutException, NoSuchWindowException) as e:
                    is_window_gone = isinstance(e, NoSuchWindowException)
                    if is_window_gone:
                        print(f"[W{worker_id}] [!] Cửa sổ đóng, tạo lại driver...")
                        try:
                            if driver:
                                try:
                                    driver.quit()
                                except Exception:
                                    pass
                                driver = None
                            driver = _create_driver(headless=headless)
                            if USE_UNDETECTED:
                                time.sleep(3)
                            _safe_get_url(driver, BASE_URL)
                            time.sleep(2)
                            _hide_video_overlay(driver)
                            _log_cloudflare_status(driver, worker_id)
                        except Exception as init_err:
                            print(f"[W{worker_id}] [!] Không tạo lại được driver: {init_err}")
                            driver = None
                            retry_count = MAX_RETRY_PER_PHONE + 1
                            if not_completed_path and not_completed_lock is not None:
                                with not_completed_lock:
                                    Path(not_completed_path).open("a", encoding="utf-8").write(phone + "\n")
                            i += 1
                            break
                    retry_count += 1
                    print(f"[W{worker_id}] [!] Timeout load trang (retry {retry_count}/{MAX_RETRY_PER_PHONE})")
                    if retry_count > MAX_RETRY_PER_PHONE:
                        if not_completed_path and not_completed_lock is not None:
                            with not_completed_lock:
                                Path(not_completed_path).open("a", encoding="utf-8").write(phone + "\n")
                        i += 1
                        break
                except Exception as e:
                    err_str = str(e)
                    is_connection_lost = (
                        "Connection refused" in err_str
                        or "Max retries exceeded" in err_str
                        or "ConnectionResetError" in err_str
                        or "Connection reset" in err_str
                        or "RemoteDisconnected" in err_str
                        or "Remote end closed" in err_str
                        or "Connection aborted" in err_str
                        or "ProtocolError" in err_str
                        or "Read timed out" in err_str
                        or "timed out" in err_str.lower()
                    )
                    if is_connection_lost:
                        print(f"[W{worker_id}] [!] Chrome đã thoát, tạo lại driver...")
                        new_driver = None
                        for recreate_attempt in range(3):
                            try:
                                if driver:
                                    try:
                                        driver.quit()
                                    except Exception:
                                        pass
                                    driver = None
                                new_driver = _create_driver(headless=headless)
                                if USE_UNDETECTED:
                                    time.sleep(3)
                                _safe_get_url(new_driver, BASE_URL)
                                time.sleep(2)
                                _hide_video_overlay(new_driver)
                                _log_cloudflare_status(new_driver, worker_id)
                                driver = new_driver
                                retry_count += 1
                                if retry_count <= MAX_RETRY_PER_PHONE:
                                    time.sleep(2)
                                    break
                            except Exception as init_err:
                                print(f"[W{worker_id}] [!] Không tạo lại được driver ({recreate_attempt + 1}/3): {init_err}")
                                if recreate_attempt < 2:
                                    time.sleep(12)
                        if driver is None:
                            retry_count = MAX_RETRY_PER_PHONE + 1
                    else:
                        print(f"[W{worker_id}] [!] Lỗi với {phone}: {e}")
                        retry_count += 1
                    if retry_count > MAX_RETRY_PER_PHONE:
                        if not_completed_path and not_completed_lock is not None:
                            with not_completed_lock:
                                Path(not_completed_path).open("a", encoding="utf-8").write(phone + "\n")
                        i += 1
                        break

        print(f"[W{worker_id}] [*] Hoàn thành {total} số trong chunk.")
    finally:
        if driver:
            def _do_quit():
                try:
                    driver.quit()
                except BaseException:
                    pass
            t = threading.Thread(target=_do_quit, daemon=True)
            t.start()
            t.join(timeout=2)  # Chờ tối đa 2s, tránh block lâu khi Ctrl+C


def run(workers: int = 1, headless: bool = False, continuous: bool = False, reload_interval: int = 60):
    """Chạy tool - 1 luồng hoặc nhiều luồng song song."""
    from multiprocessing import Manager

    total_processed = 0
    batch_num = 0

    script_dir = Path(__file__).parent
    completed_path = script_dir / "completed.txt"
    while True:
        phones = load_phones(path=str(script_dir / "phones.txt"), exclude_done_path=str(completed_path))
        if not phones:
            if continuous:
                print(f"[*] phones.txt rỗng. Đợi {reload_interval}s rồi load lại...")
                time.sleep(reload_interval)
                continue
            print("[!] Tạo file phones.txt với mỗi dòng 1 số điện thoại.")
            return

        batch_num += 1
        if continuous:
            print(f"\n[*] === Batch {batch_num} ===")
        print(f"[*] Đã load {len(phones)} số điện thoại.")
        script_dir = Path(__file__).parent
        not_completed_path = str(script_dir / "not_completed.txt")
        completed_path = str(script_dir / "completed.txt")
        print(f"[*] Số hoàn thành ghi vào: {completed_path} (resume khi restart)")
        print(f"[*] Số không hoàn thành sẽ ghi vào: {not_completed_path}")

        if workers <= 1:
            run_worker(0, phones, headless=headless, completed_path=completed_path)
        else:
            # Chia đều SĐT cho N luồng
            chunk_size = (len(phones) + workers - 1) // workers
            chunks = [
                phones[i : i + chunk_size]
                for i in range(0, len(phones), chunk_size)
            ]
            while len(chunks) < workers:
                chunks.append([])
            chunks = chunks[:workers]

            stagger_delay = 10.0 if workers >= 4 else (8.0 if workers >= 2 else 0)
            print(f"[*] Chạy {workers} luồng song song" + (f" (stagger {stagger_delay}s)" if stagger_delay else "") + "...")

            manager = Manager()
            completed_counter = manager.Value("i", 0)
            not_completed_lock = manager.Lock()
            completed_lock = manager.Lock()
            processes = []
            for wid, chunk in enumerate(chunks):
                if not chunk:
                    continue
                p = Process(
                    target=run_worker,
                    args=(wid + 1, chunk, headless, stagger_delay * wid),
                    kwargs={
                        "completed_counter": completed_counter,
                        "not_completed_path": not_completed_path,
                        "not_completed_lock": not_completed_lock,
                        "completed_path": completed_path,
                        "completed_lock": completed_lock,
                    },
                )
                p.start()
                processes.append(p)

            try:
                last_summary = time.time()
                while any(p.is_alive() for p in processes):
                    for p in processes:
                        p.join(timeout=1)
                    if SUMMARY_INTERVAL and (time.time() - last_summary) >= SUMMARY_INTERVAL:
                        last_summary = time.time()
                        print(f"\n[*] === Tổng kết: Đã hoàn thành {completed_counter.value} số ===\n")
            except KeyboardInterrupt:
                print("\n[*] Đang dừng các worker...")
                for p in processes:
                    p.terminate()
                for p in processes:
                    p.join(timeout=3)
                raise

        total_processed += len(phones)
        if workers > 1:
            print(f"\n[*] === Tổng kết: Đã hoàn thành {completed_counter.value} số ===\n")
        else:
            print(f"\n[*] Hoàn thành batch {batch_num}.\n")

        if not continuous:
            break
        print(f"[*] Đợi {reload_interval}s rồi load phones.txt tiếp...")
        time.sleep(reload_interval)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PNJ Thần Tài - Tích Lộc Automation")
    parser.add_argument("--workers", "-w", type=int, default=NUM_WORKERS,
                        help=f"Số luồng chạy song song (mặc định: {NUM_WORKERS})")
    parser.add_argument("--headless", action="store_true", help="Chạy Chrome ẩn (tiết kiệm RAM)")
    parser.add_argument("--continuous", "-c", action="store_true",
                        help="Chạy liên tục: khi hết phones, đợi và load lại phones.txt")
    parser.add_argument("--reload-interval", type=int, default=60,
                        help="Giây chờ trước khi load lại phones.txt (mặc định: 60)")
    args = parser.parse_args()
    try:
        run(workers=args.workers, headless=args.headless, continuous=args.continuous,
            reload_interval=args.reload_interval)
    except KeyboardInterrupt:
        print("\n[*] Đã dừng (Ctrl+C).")
