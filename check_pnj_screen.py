#!/usr/bin/env python3
"""
Kiểm tra bao nhiêu VPS đang chạy screen session "pnj" (tool PNJ Thần Tài).
SSH vào từng VPS, chạy screen -ls | grep pnj → nếu có thì đang chạy.

Đầu vào: file check_vps.txt (IP + password), mỗi dòng "IP<Tab hoặc Space>Password"
Chạy: python check_pnj_screen.py
       python check_pnj_screen.py --file check_vps.txt --workers 80
"""
from pathlib import Path
import argparse
import logging
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import paramiko
except ImportError:
    print("Thiếu thư viện paramiko. Chạy: pip install paramiko")
    sys.exit(1)

logging.getLogger("paramiko").setLevel(logging.CRITICAL)

DIR = Path(__file__).parent
USER = "root"
# Lệnh kiểm tra: có session tên pnj (Detached/Attached) = đang chạy
CHECK_CMD = "screen -ls 2>/dev/null | grep -q 'pnj'"
SSH_TIMEOUT = 10

print_lock = threading.Lock()


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


def check_one(args: tuple) -> tuple[int, str, bool]:
    """(index_0based, ip, password) -> (index, ip, is_running)."""
    idx, ip, password = args
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            hostname=ip,
            port=22,
            username=USER,
            password=password,
            timeout=SSH_TIMEOUT,
            allow_agent=False,
            look_for_keys=False,
        )
        _, stdout, _ = client.exec_command(CHECK_CMD, timeout=5)
        code = stdout.channel.recv_exit_status()
        client.close()
        return (idx, ip, code == 0)
    except Exception:
        return (idx, ip, False)


def main():
    parser = argparse.ArgumentParser(description="Kiểm tra VPS nào đang chạy screen pnj")
    parser.add_argument(
        "-f", "--file",
        type=Path,
        default=DIR / "check_vps.txt",
        help="File IP và password (mặc định: check_vps.txt)",
    )
    parser.add_argument(
        "-w", "--workers",
        type=int,
        default=80,
        help="Số kết nối kiểm tra đồng thời (mặc định: 80)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="In từng IP: đang chạy / không chạy",
    )
    args = parser.parse_args()
    path = args.file if args.file.is_absolute() else DIR / args.file
    workers = max(1, min(args.workers, 200))

    servers = load_servers(path)
    if not servers:
        print(f"[!] Không có dòng nào trong {path}")
        sys.exit(1)

    n = len(servers)
    print(f"[*] Đang kiểm tra {n} VPS (screen pnj)...")
    print(f"[*] Số luồng: {min(n, workers)}")
    print()

    tasks = [(i, ip, pwd) for i, (ip, pwd) in enumerate(servers)]
    running = []
    not_running = []

    with ThreadPoolExecutor(max_workers=min(n, workers)) as ex:
        futures = {ex.submit(check_one, t): t for t in tasks}
        for fut in as_completed(futures):
            idx, ip, ok = fut.result()
            if ok:
                running.append((idx, ip))
                if args.verbose:
                    with print_lock:
                        print(f"  [OK] {ip}")
            else:
                not_running.append((idx, ip))
                if args.verbose:
                    with print_lock:
                        print(f"  [--] {ip}")

    running.sort(key=lambda x: x[0])
    not_running.sort(key=lambda x: x[0])

    print()
    print(f"[*] Kết quả: {len(running)}/{n} VPS đang chạy screen pnj")
    if not_running and not args.verbose:
        print(f"[*] Không chạy ({len(not_running)}): ", end="")
        print(", ".join(ip for _, ip in not_running[:20]), end="")
        if len(not_running) > 20:
            print(f" ... và {len(not_running) - 20} VPS khác")
        else:
            print()
    if running and args.verbose:
        print(f"[*] Đang chạy: {[ip for _, ip in running]}")


if __name__ == "__main__":
    main()
