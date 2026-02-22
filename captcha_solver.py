"""
Giải captcha: 2Captcha API, ddddocr, hoặc Tesseract OCR.
Trên Windows: pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'
"""
import base64
import re
import os
import time
from collections import Counter
import cv2
import numpy as np
import pytesseract
import requests
from PIL import Image
from io import BytesIO
from typing import Optional


# Đường dẫn Tesseract (chỉnh nếu cần, ví dụ Windows)
TESSERACT_CMD = os.environ.get("TESSERACT_CMD")
if TESSERACT_CMD:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD


def solve_captcha_2captcha(image_bytes: bytes, api_key: str) -> Optional[str]:
    """Giải captcha qua 2Captcha API. Cần đăng ký và nạp tiền tại 2captcha.com"""
    try:
        b64 = base64.b64encode(image_bytes).decode()
        if len(b64) > 100_000:  # API giới hạn ~100KB
            img = Image.open(BytesIO(image_bytes))
            img.thumbnail((300, 100))
            buf = BytesIO()
            img.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode()

        r = requests.post(
            "https://api.2captcha.com/createTask",
            json={
                "clientKey": api_key,
                "task": {"type": "ImageToTextTask", "body": b64, "case": True},
            },
            timeout=30,
        )
        data = r.json()
        if data.get("errorId") != 0:
            print(f"[2Captcha] Lỗi: {data.get('errorDescription', data)}")
            return None

        task_id = data.get("taskId")
        for _ in range(40):  # ~2 phút, poll mỗi 3s
            time.sleep(3)
            r2 = requests.post(
                "https://api.2captcha.com/getTaskResult",
                json={"clientKey": api_key, "taskId": task_id},
                timeout=30,
            )
            res = r2.json()
            if res.get("status") == "ready":
                solution = res.get("solution") or {}
                return (solution.get("text") or "").strip()
            if res.get("errorId") != 0:
                return None
        return None
    except Exception as e:
        print(f"[2Captcha] Lỗi: {e}")
        return None


def _scale_for_ocr(img_array: np.ndarray, min_height: int = 80) -> np.ndarray:
    """Phóng to ảnh nhỏ để Tesseract nhận dạng tốt hơn."""
    h, w = img_array.shape[:2]
    if h < min_height:
        scale = min_height / h
        new_w = int(w * scale)
        return cv2.resize(img_array, (new_w, min_height), interpolation=cv2.INTER_CUBIC)
    return img_array


def _preprocess_for_ddddocr(img_array: np.ndarray) -> list[bytes]:
    """Tạo các biến thể ảnh để thử với ddddocr (PNG bytes). Captcha nhiễu chấm/đường."""
    if len(img_array.shape) == 3:
        gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
    else:
        gray = img_array.copy()
    gray = _scale_for_ocr(gray, min_height=80)
    results = []
    buf = BytesIO()

    # 1. Raw - ddddocr xử lý tốt ảnh gốc
    pil = Image.fromarray(gray)
    pil.save(buf, format="PNG")
    results.append(buf.getvalue())
    buf.seek(0)
    buf.truncate(0)

    # 2. Giảm nhiễu chấm (median) + tăng contrast
    denoised = cv2.medianBlur(gray, 3)
    denoised = cv2.convertScaleAbs(denoised, alpha=1.3, beta=5)
    pil = Image.fromarray(denoised)
    pil.save(buf, format="PNG")
    results.append(buf.getvalue())
    buf.seek(0)
    buf.truncate(0)

    # 3. Bilateral (giữ cạnh, giảm nhiễu)
    bil = cv2.bilateralFilter(gray, 5, 50, 50)
    bil = cv2.convertScaleAbs(bil, alpha=1.4, beta=5)
    pil = Image.fromarray(bil)
    pil.save(buf, format="PNG")
    results.append(buf.getvalue())

    return results


def _preprocess_variants(img_array: np.ndarray) -> list[tuple[np.ndarray, str]]:
    """Tạo nhiều biến thể tiền xử lý cho captcha nhiễu (nền chấm, chữ nghiêng)."""
    if len(img_array.shape) == 3:
        gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
    else:
        gray = img_array.copy()

    gray = _scale_for_ocr(gray, min_height=150)
    results = []

    # 1. Giảm nhiễu nền (bilateral giữ cạnh chữ)
    denoised = cv2.bilateralFilter(gray, 5, 50, 50)
    # Tăng contrast
    denoised = cv2.convertScaleAbs(denoised, alpha=1.5, beta=5)
    _, th1 = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    results.append((th1, "bilateral_otsu"))

    # 2. Adaptive threshold - tốt cho nền không đều
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    th2 = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    results.append((th2, "adaptive"))

    # 3. Denoise mạnh rồi Otsu
    denoise2 = cv2.fastNlMeansDenoising(gray, None, 12, 7, 21)
    denoise2 = cv2.convertScaleAbs(denoise2, alpha=1.4, beta=0)
    _, th3 = cv2.threshold(denoise2, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # Loại bỏ chấm nhỏ ( morphological open)
    kernel = np.ones((2, 2), np.uint8)
    th3 = cv2.morphologyEx(th3, cv2.MORPH_OPEN, kernel)
    results.append((th3, "denoise_otsu"))

    # 4. Otsu trên ảnh gốc đã scale
    gray2 = cv2.convertScaleAbs(gray, alpha=1.3, beta=10)
    _, th4 = cv2.threshold(gray2, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    results.append((th4, "otsu"))

    # 5. Đảo màu (chữ trắng nền đen)
    results.append((255 - th1, "inverted"))

    # 6. CLAHE - tăng contrast cục bộ cho chữ mờ
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(2, 2))
    gray_clahe = clahe.apply(gray)
    _, th6 = cv2.threshold(gray_clahe, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    results.append((th6, "clahe"))

    # 7. Fixed threshold (chữ tối trên nền sáng)
    _, th7 = cv2.threshold(denoised, 127, 255, cv2.THRESH_BINARY)
    results.append((th7, "fixed127"))

    # 8. Median blur - loại nhiễu chấm tốt (captcha nền chấm)
    median = cv2.medianBlur(gray, 3)
    median = cv2.convertScaleAbs(median, alpha=1.4, beta=5)
    _, th8 = cv2.threshold(median, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    kernel = np.ones((2, 2), np.uint8)
    th8 = cv2.morphologyEx(th8, cv2.MORPH_OPEN, kernel)
    results.append((th8, "median_otsu"))

    return results


def preprocess_captcha_image(img_array: np.ndarray) -> np.ndarray:
    """Tiền xử lý mặc định (tương thích cũ)."""
    variants = _preprocess_variants(img_array)
    return variants[0][0]


def _ocr_image(pil_img: Image.Image, config: str) -> Optional[str]:
    """Chạy Tesseract với config cho trước."""
    text = pytesseract.image_to_string(pil_img, config=config)
    return re.sub(r"[^a-zA-Z0-9]", "", text).strip()


def _solve_captcha_ddddocr(image_bytes: bytes) -> Optional[str]:
    """Giải captcha bằng ddddocr - thử raw + nhiều biến thể preprocess, voting."""
    try:
        import ddddocr
        ocr = ddddocr.DdddOcr(show_ad=False)
        candidates: list[str] = []

        # 1. Raw
        try:
            t = ocr.classification(image_bytes)
            if t:
                candidates.append(t.strip())
        except Exception:
            pass

        # 2. Preprocessed variants (cho captcha nhiễu chấm/đường)
        try:
            img = Image.open(BytesIO(image_bytes))
            arr = np.array(img)
            for var_bytes in _preprocess_for_ddddocr(arr):
                try:
                    t = ocr.classification(var_bytes)
                    if t:
                        candidates.append(t.strip())
                except Exception:
                    pass
        except Exception:
            pass

        if not candidates:
            return None
        # Voting: ưu tiên kết quả 6 ký tự (captcha PNJ thường 6 chars)
        six_char = [c for c in candidates if len(c) == 6]
        if six_char:
            cnt = Counter(six_char)
            return cnt.most_common(1)[0][0]
        return candidates[0]
    except ImportError:
        return None
    except Exception as e:
        print(f"[ddddocr] Lỗi: {e}")
        return None


def solve_captcha_from_bytes(
    image_bytes: bytes, api_key: Optional[str] = None, use_ddddocr: bool = True
) -> Optional[str]:
    """
    Giải captcha. Thứ tự: 2Captcha API (nếu có key) -> ddddocr (miễn phí) -> Tesseract.
    """
    if api_key:
        text = solve_captcha_2captcha(image_bytes, api_key)
        if text:
            return text

    if use_ddddocr:
        text = _solve_captcha_ddddocr(image_bytes)
        if text:
            return text

    return _solve_captcha_ocr(image_bytes)


def _solve_captcha_ocr(image_bytes: bytes) -> Optional[str]:
    """
    Nhận ảnh captcha bằng Tesseract. Thử nhiều biến thể tiền xử lý (nền nhiễu, chữ nghiêng).
    """
    whitelist = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    configs = [
        f"--oem 3 --psm 7 -c tessedit_char_whitelist={whitelist}",
        f"--oem 3 --psm 8 -c tessedit_char_whitelist={whitelist}",
        f"--oem 3 --psm 13 -c tessedit_char_whitelist={whitelist}",
        f"--oem 1 --psm 7 -c tessedit_char_whitelist={whitelist}",
    ]

    try:
        img = Image.open(BytesIO(image_bytes))
        img_array = np.array(img)
        candidates: list[str] = []
        seen: set[str] = set()

        # Thử tất cả biến thể preprocess
        for arr, _ in _preprocess_variants(img_array):
            pil_img = Image.fromarray(arr)
            for cfg in configs:
                text = _ocr_image(pil_img, cfg)
                if text and 4 <= len(text) <= 10 and text not in seen:
                    seen.add(text)
                    candidates.append(text)

        # Thử ảnh gốc scale
        gray = img_array
        if len(gray.shape) == 3:
            gray = cv2.cvtColor(gray, cv2.COLOR_BGR2GRAY)
        gray = _scale_for_ocr(gray, min_height=150)
        pil_gray = Image.fromarray(gray)
        for cfg in configs:
            text = _ocr_image(pil_gray, cfg)
            if text and 4 <= len(text) <= 10 and text not in seen:
                seen.add(text)
                candidates.append(text)

        # Ưu tiên 6 ký tự, thử sửa lỗi OCR thường gặp: 3/S, j/y
        best = next((t for t in candidates if len(t) == 6), candidates[0] if candidates else None)
        if not best:
            return None
        if len(best) == 6 and best[0] in ("S", "5") and best[1:].islower():
            return "3" + best[1:]
        return best

    except Exception as e:
        print(f"[Captcha] Lỗi: {e}")
        return None


def solve_captcha_from_element(element_image_src: Optional[str], driver) -> Optional[str]:
    """
    Lấy ảnh captcha từ element (src URL hoặc screenshot), giải và trả về text.
    """
    try:
        # Thử lấy từ src
        if element_image_src and element_image_src.startswith("data:"):
            # base64
            import base64
            if "base64," in element_image_src:
                b64 = element_image_src.split("base64,")[1]
                img_bytes = base64.b64decode(b64)
                return solve_captcha_from_bytes(img_bytes)
        elif element_image_src and (element_image_src.startswith("http") or element_image_src.startswith("//")):
            import requests
            url = element_image_src if element_image_src.startswith("http") else "https:" + element_image_src
            r = requests.get(url, timeout=10)
            if r.ok:
                return solve_captcha_from_bytes(r.content)
    except Exception as e:
        print(f"[Captcha] Lỗi lấy từ src: {e}")

    return None
