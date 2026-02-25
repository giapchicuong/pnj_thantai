#!/usr/bin/env python3
"""
Deploy PNJ Thần Tài lên 40 VPS đồng loạt qua SSH (paramiko + đa luồng).
Chạy trên máy local: python deploy_all.py

Đầu vào:
  - servers.txt: mỗi dòng "IP<Tab>Password" (user mặc định root)
  - keys.txt: mỗi dòng 1 TMProxy API key (key thứ i ghép với VPS thứ i)

Cài đặt: pip install paramiko
"""
from pathlib import Path
import sys
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

# Tắt log traceback của paramiko (chỉ in lỗi gọn ra màn hình)
logging.getLogger("paramiko").setLevel(logging.CRITICAL)

try:
    import paramiko
except ImportError:
    print("Thiếu thư viện paramiko. Chạy: pip install paramiko")
    sys.exit(1)

DIR = Path(__file__).parent
SERVERS_FILE = DIR / "servers.txt"
KEYS_FILE = DIR / "keys.txt"
USER = "root"
MAX_WORKERS = 10  # Giảm luồng để tránh "Connection reset by peer" khi nhiều SSH cùng lúc
SSH_RETRIES = 3  # Số lần thử lại khi SSH lỗi (banner / connection reset)
SSH_RETRY_DELAY = 2  # Giây chờ giữa mỗi lần retry


def load_servers(path: Path) -> list[tuple[str, str]]:
    """Trả về list (ip, password)."""
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").strip().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t", 1)
        ip = (parts[0] or "").strip()
        pwd = (parts[1] or "").strip() if len(parts) > 1 else ""
        if ip:
            out.append((ip, pwd))
    return out


def load_keys(path: Path) -> list[str]:
    """Trả về list API key (mỗi dòng 1 key)."""
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
    """Escape string để đặt trong single quotes bash: '...'."""
    return s.replace("'", "'\"'\"'")


def deploy_one(args: tuple) -> tuple[int, str, str, bool, str]:
    """
    Thực thi deploy trên 1 VPS: upload phones_{idx}.txt từ local lên ~/pnj_thantai/phones.txt rồi chạy start_pnj.sh.
    args = (index_1based, ip, password, api_key).
    Trả về (index, ip, status, ok, message).
    """
    idx, ip, password, api_key = args
    label = f"VPS {idx} - {ip}"
    local_phones = DIR / f"phones_{idx}.txt"
    if not local_phones.is_file():
        return (idx, ip, label, False, f"Không tìm thấy file local: phones_{idx}.txt")

    last_error = None
    for attempt in range(SSH_RETRIES):
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
            # Upload file local phones_{idx}.txt -> remote ~/pnj_thantai/phones.txt
            sftp = client.open_sftp()
            remote_path = "/root/pnj_thantai/phones.txt"
            sftp.put(str(local_phones), remote_path)
            sftp.close()

            safe_key = escape_bash_single(api_key)
            cmd = (
                "screen -S pnj -X quit 2>/dev/null || true; "
                "cd ~/pnj_thantai && "
                f"export TMPROXY_API_KEY='{safe_key}' && "
                "bash start_pnj.sh"
            )
            stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
            err = stderr.read().decode("utf-8", errors="replace").strip()
            out = stdout.read().decode("utf-8", errors="replace").strip()
            code = stdout.channel.recv_exit_status()
            client.close()

            if code != 0:
                msg = err or out or f"exit code {code}"
                return (idx, ip, label, False, msg)
            return (idx, ip, label, True, "Triển khai thành công")
        except paramiko.AuthenticationException as e:
            return (idx, ip, label, False, f"Sai mật khẩu / auth: {e}")
        except (paramiko.SSHException, ConnectionResetError, OSError) as e:
            last_error = e
            if attempt < SSH_RETRIES - 1:
                time.sleep(SSH_RETRY_DELAY)
            continue
        except Exception as e:
            return (idx, ip, label, False, str(e))

    return (idx, ip, label, False, f"SSH lỗi (đã thử {SSH_RETRIES} lần): {last_error}")


def main():
    servers = load_servers(SERVERS_FILE)
    keys = load_keys(KEYS_FILE)

    if not servers:
        print(f"[!] Chưa có dữ liệu trong {SERVERS_FILE}")
        print("    Format mỗi dòng: IP<Tab>Password")
        sys.exit(1)
    if not keys:
        print(f"[!] Chưa có dữ liệu trong {KEYS_FILE}")
        print("    Mỗi dòng 1 TMProxy API key")
        sys.exit(1)

    n = min(len(servers), len(keys), 40)
    if n < len(servers) or n < len(keys):
        print(f"[*] Dùng {n} cặp (servers: {len(servers)}, keys: {len(keys)})")

    tasks = []
    for i in range(n):
        ip, pwd = servers[i]
        key = keys[i]
        tasks.append((i + 1, ip, pwd, key))

    print(f"[*] Đang deploy lên {n} VPS (tối đa {MAX_WORKERS} luồng)...")
    print()

    ok_count = 0
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = {ex.submit(deploy_one, t): t for t in tasks}
        for fut in as_completed(futures):
            idx, ip, label, ok, msg = fut.result()
            if ok:
                ok_count += 1
                print(f"[{label}] Triển khai thành công")
            else:
                print(f"[{label}] Lỗi: {msg}")

    print()
    print(f"[*] Xong: {ok_count}/{n} VPS thành công.")


if __name__ == "__main__":
    main()
