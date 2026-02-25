#!/usr/bin/env python3
"""
Cài đặt và khởi động tool PNJ Thần Tài lên N VPS Ubuntu mới (đa luồng).
Chạy từ file SĐT số 48 trở đi: phones_48.txt, phones_49.txt, ... (40 VPS = 48..87).

Chạy trên máy local: python deploy_new_7_vps.py

Đầu vào:
  - new_servers.txt: 40 dòng, mỗi dòng "IP<Tab hoặc Space>Password" (user: root)
  - new_keys.txt: 40 dòng, mỗi dòng 1 TMProxy API key
  - phones_48.txt .. phones_87.txt: file SĐT (VPS 1 dùng phones_48, VPS 40 dùng phones_87)

Mỗi VPS dùng link roadshow (MBC/MTG/TNN/DNB/HCM/MTY) theo (i-1) % 6, giống deploy_all (config.py BASE_URL_INDEX).

Cài đặt: pip install paramiko
"""
from pathlib import Path
import sys
import time
import threading
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

logging.getLogger("paramiko").setLevel(logging.CRITICAL)

try:
    import paramiko
except ImportError:
    print("Thiếu thư viện paramiko. Chạy: pip install paramiko")
    sys.exit(1)

DIR = Path(__file__).parent
NEW_SERVERS_FILE = DIR / "new_servers.txt"
NEW_KEYS_FILE = DIR / "new_keys.txt"
USER = "root"
DEPLOY_SCRIPT_URL = "https://raw.githubusercontent.com/giapchicuong/pnj_thantai/main/deploy_vps.sh"
SUCCESS_MARKER = "=== Deploy xong ==="
MAX_INSTALL_ATTEMPTS = 10
INSTALL_RETRY_DELAY = 5
REMOTE_PHONES_PATH = "/root/pnj_thantai/phones.txt"
# Bắt đầu từ file phones_48.txt (VPS 1 = phones_48, VPS 40 = phones_87)
START_PHONE_NUM = 48
# 6 link roadshow (MBC, MTG, TNN, DNB, HCM, MTY) – VPS i dùng (i-1) % 6
NUM_BASE_URLS = 6

print_lock = threading.Lock()


def log(label: str, msg: str) -> None:
    with print_lock:
        print(f"[{label}] {msg}", flush=True)


def load_servers(path: Path) -> list[tuple[str, str]]:
    """Trả về list (ip, password)."""
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").strip().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.replace("\t", " ").split(None, 1)
        ip = (parts[0] or "").strip()
        pwd = (parts[1] or "").strip() if len(parts) > 1 else ""
        if ip:
            out.append((ip, pwd))
    return out


def load_keys(path: Path) -> list[str]:
    """Trả về list API key."""
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").strip().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        out.append(line)
    return out


def escape_bash_single(s: str) -> str:
    return s.replace("'", "'\"'\"'")


def deploy_one(args: tuple) -> tuple[int, str, bool, list[str]]:
    """
    args = (index_1_based, ip, password, api_key). index 1 = phones_START_PHONE_NUM.
    Trả về (index, ip, ok, list_message).
    """
    idx, ip, password, api_key = args
    file_idx = START_PHONE_NUM + (idx - 1)  # VPS 1 = phones_48, VPS 40 = phones_87
    label = f"VPS {file_idx} - {ip}"
    local_phones = DIR / f"phones_{file_idx}.txt"
    messages = []

    if not local_phones.is_file():
        messages.append(f"Lỗi: Không tìm thấy file local phones_{file_idx}.txt")
        return (idx, ip, False, messages)

    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            hostname=ip,
            port=22,
            username=USER,
            password=password,
            timeout=15,
            allow_agent=False,
            look_for_keys=False,
        )

        # --- BƯỚC 1: Cài đặt (retry đến khi stdout chứa "=== Deploy xong ===") ---
        messages.append("Đang cài đặt...")
        install_ok = False
        for attempt in range(1, MAX_INSTALL_ATTEMPTS + 1):
            stdin, stdout, stderr = client.exec_command(
                f"curl -sL {DEPLOY_SCRIPT_URL} | bash",
                timeout=600,
            )
            out = stdout.read().decode("utf-8", errors="replace")
            err = stderr.read().decode("utf-8", errors="replace")
            code = stdout.channel.recv_exit_status()

            if SUCCESS_MARKER in out:
                install_ok = True
                messages.append(f"Cài đặt thành công (sau {attempt} lần thử).")
                break
            if attempt < MAX_INSTALL_ATTEMPTS:
                time.sleep(INSTALL_RETRY_DELAY)
                messages.append(f"Cài đặt chưa xong (lần {attempt}), thử lại...")

        if not install_ok:
            messages.append(f"Cài đặt thất bại sau {MAX_INSTALL_ATTEMPTS} lần (không thấy '{SUCCESS_MARKER}').")
            client.close()
            return (idx, ip, False, messages)

        # --- BƯỚC 2: Upload file SĐT ---
        sftp = client.open_sftp()
        sftp.put(str(local_phones), REMOTE_PHONES_PATH)
        sftp.close()
        messages.append(f"Đã upload file phones_{file_idx}.txt")

        # --- BƯỚC 3: Chạy tool (BASE_URL_INDEX để config.py chọn đúng link) ---
        url_index = (idx - 1) % NUM_BASE_URLS
        safe_key = escape_bash_single(api_key)
        cmd = (
            f"export TMPROXY_API_KEY='{safe_key}' && "
            f"export BASE_URL_INDEX='{url_index}' && "
            "cd ~/pnj_thantai && bash start_pnj.sh"
        )
        stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
        stdout.channel.recv_exit_status()
        client.close()
        messages.append("Đã khởi động tool.")

        return (idx, ip, True, messages)

    except paramiko.AuthenticationException as e:
        messages.append(f"Sai mật khẩu / auth: {e}")
        return (idx, ip, False, messages)
    except Exception as e:
        messages.append(f"Lỗi: {e}")
        return (idx, ip, False, messages)


def main():
    servers = load_servers(NEW_SERVERS_FILE)
    keys = load_keys(NEW_KEYS_FILE)

    n = min(len(servers), len(keys))
    if n == 0:
        print(f"[!] Chưa có dữ liệu trong {NEW_SERVERS_FILE} hoặc {NEW_KEYS_FILE}")
        sys.exit(1)

    tasks = []
    for i in range(n):
        ip, pwd = servers[i]
        key = keys[i]
        tasks.append((i + 1, ip, pwd, key))

    last_file = START_PHONE_NUM + n - 1
    print(f"[*] Đang deploy {n} VPS (phones_{START_PHONE_NUM}.txt .. phones_{last_file}.txt)...")
    print()

    ok_count = 0
    with ThreadPoolExecutor(max_workers=min(n, 20)) as ex:
        futures = {ex.submit(deploy_one, t): t for t in tasks}
        for fut in as_completed(futures):
            idx, ip, ok, messages = fut.result()
            file_idx = START_PHONE_NUM + (idx - 1)
            label = f"VPS {file_idx} - {ip}"
            for msg in messages:
                log(label, msg)
            if ok:
                ok_count += 1
            else:
                log(label, "Kết quả: THẤT BẠI")

    print()
    print(f"[*] Xong: {ok_count}/{n} VPS thành công.")


if __name__ == "__main__":
    main()
