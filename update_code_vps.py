#!/usr/bin/env python3
"""
Cập nhật code trên các VPS đã chạy: git pull + khởi động lại tool.
Trên mỗi VPS: git fetch + reset --hard origin/main (luôn lấy code mới nhất, tránh overwrite) rồi khởi động lại.

Đầu vào: vps_1_248.txt (IP + password, mỗi dòng)

Chạy: python update_code_vps.py
       python update_code_vps.py -s vps_1_248.txt -w 80
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
SSH_TIMEOUT = 15
# git pull có thể lâu, start_pnj nhanh
CMD_TIMEOUT = 120

print_lock = threading.Lock()


def load_servers(path: Path) -> list[tuple[str, str]]:
    out = []
    if not path.exists():
        return out
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


def update_one(args: tuple) -> tuple[int, str, bool, str]:
    """(index_0based, ip, password) -> (index, ip, ok, message)."""
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
        cmd = (
            "cd ~/pnj_thantai && git fetch origin && git reset --hard origin/main && "
            "screen -S pnj -X quit 2>/dev/null || true && "
            "bash start_pnj.sh"
        )
        _, stdout, stderr = client.exec_command(cmd, timeout=CMD_TIMEOUT)
        out = stdout.read().decode("utf-8", errors="replace")
        err = stderr.read().decode("utf-8", errors="replace")
        code = stdout.channel.recv_exit_status()
        client.close()
        if code == 0:
            return (idx, ip, True, "Đã cập nhật và khởi động lại.")
        return (idx, ip, False, (err or out or f"exit {code}").strip()[:250])
    except Exception as e:
        return (idx, ip, False, str(e)[:250])


def main():
    parser = argparse.ArgumentParser(description="Cập nhật code (git pull) + khởi động lại tool trên VPS")
    parser.add_argument(
        "-s", "--servers",
        type=Path,
        default=DIR / "vps_1_248.txt",
        help="File IP + password (mặc định: vps_1_248.txt)",
    )
    parser.add_argument(
        "-n", "--limit",
        type=int,
        default=0,
        help="Chỉ chạy N VPS đầu (0 = tất cả). VD: 248",
    )
    parser.add_argument(
        "-w", "--workers",
        type=int,
        default=80,
        help="Số VPS xử lý đồng thời (mặc định: 80)",
    )
    args = parser.parse_args()
    servers_path = args.servers if args.servers.is_absolute() else DIR / args.servers
    workers = max(1, min(args.workers, 150))

    servers = load_servers(servers_path)
    if not servers:
        print(f"[!] Không có dữ liệu trong {servers_path}")
        sys.exit(1)

    n = len(servers)
    if args.limit > 0:
        n = min(n, args.limit)
    if n == 0:
        print("[!] Không có VPS nào.")
        sys.exit(1)

    tasks = [(i, servers[i][0], servers[i][1]) for i in range(n)]

    print(f"[*] Cập nhật code (git pull) + khởi động lại trên {n} VPS...")
    print(f"[*] Số luồng: {min(n, workers)}")
    print()

    ok_count = 0
    with ThreadPoolExecutor(max_workers=min(n, workers)) as ex:
        futures = {ex.submit(update_one, t): t for t in tasks}
        for fut in as_completed(futures):
            idx, ip, ok, msg = fut.result()
            with print_lock:
                if ok:
                    ok_count += 1
                    print(f"  [OK] {ip}")
                else:
                    print(f"  [FAIL] {ip}: {msg}")

    print()
    print(f"[*] Xong: {ok_count}/{n} VPS đã cập nhật và chạy lại.")


if __name__ == "__main__":
    main()
