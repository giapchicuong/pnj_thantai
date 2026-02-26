#!/usr/bin/env python3
"""
Chỉ update code + upload phones + start PNJ (KHÔNG deploy). Dùng cho server ĐÃ CÓ thư mục ~/pnj_thantai đang chạy.

Đầu vào: all_vps.txt (hoặc -s file) — mỗi dòng "IP<Tab>Password". Dòng 1 = phones_1.txt, dòng 2 = phones_2.txt, ...

Trên mỗi VPS:
  1. scp phones_{số}.txt → ~/pnj_thantai/phones.txt
  2. ssh: cd ~/pnj_thantai && git fetch origin && git reset --hard origin/main
  3. ssh: kill screen/pprocess cũ; cd ~/pnj_thantai && bash start_pnj.sh

Chạy trước script này cho các server đã chạy; sau đó chạy deploy_and_run_all.py cho server mới.

  python update_and_run_all.py
  python update_and_run_all.py -s all_vps.txt -w 80 -n 100
"""
from pathlib import Path
import argparse
import sys
import threading
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

logging.getLogger("paramiko").setLevel(logging.CRITICAL)
try:
    import paramiko
except ImportError:
    print("Thiếu paramiko. Chạy: pip install paramiko")
    sys.exit(1)

DIR = Path(__file__).parent
DEFAULT_SERVERS_FILE = DIR / "all_vps.txt"
USER = "root"
SSH_TIMEOUT = 25
START_MARKERS = (
    "[*] Khởi động PNJ trong screen",
    "[!] Session 'pnj' đã chạy",
)
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


def run_one(args: tuple) -> tuple[int, str, bool, list[str]]:
    """(index_0based, ip, password) -> (index, ip, ok, messages)."""
    idx, ip, password = args
    messages = []
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

        # 0. Chỉ xử lý VPS đã có thư mục pnj_thantai (server đang chạy)
        _, so, _ = client.exec_command("test -d /root/pnj_thantai && echo YES || echo NO", timeout=10)
        has_dir = (so.read().decode().strip() == "YES")
        if not has_dir:
            messages.append("Chưa có thư mục ~/pnj_thantai → bỏ qua (chạy deploy_and_run_all.py cho VPS này)")
            client.close()
            return (idx, ip, False, messages)

        # 1. Upload phones_{số}.txt
        file_idx = idx + 1
        local_phones = DIR / f"phones_{file_idx}.txt"
        if local_phones.is_file():
            try:
                sftp = client.open_sftp()
                sftp.put(str(local_phones), "/root/pnj_thantai/phones.txt")
                sftp.close()
                messages.append(f"Đã tải phones_{file_idx}.txt lên phones.txt")
            except Exception as e:
                messages.append(f"Upload phones_{file_idx}.txt lỗi: {e}")
        else:
            messages.append(f"Không có phones_{file_idx}.txt → bỏ qua upload")

        # 2. Git pull
        messages.append("Đang git pull...")
        _, so, se = client.exec_command(
            "cd /root/pnj_thantai && git fetch origin && git reset --hard origin/main",
            timeout=120,
        )
        code = so.channel.recv_exit_status()
        out = so.read().decode("utf-8", errors="replace")
        err = se.read().decode("utf-8", errors="replace")
        if code != 0:
            messages.append(f"Git lỗi (exit {code}): {(err or out)[:200]}")
        else:
            messages.append("Git xong.")

        # 3. Kill cũ + start_pnj.sh
        messages.append("Đang start_pnj.sh...")
        kill_cmd = (
            "screen -S pnj -X quit 2>/dev/null || true; "
            "pkill -f 'run_16gb.sh|start_pnj.sh|main.py.*pnj' 2>/dev/null || true"
        )
        _, so_kill, _ = client.exec_command(kill_cmd, timeout=15)
        so_kill.channel.recv_exit_status()
        time.sleep(1)

        stdin, stdout, stderr = client.exec_command(
            "cd /root/pnj_thantai && bash start_pnj.sh",
            timeout=30,
            get_pty=True,
        )
        out = stdout.read().decode("utf-8", errors="replace")
        err = stderr.read().decode("utf-8", errors="replace")
        code = stdout.channel.recv_exit_status()
        combined = out + "\n" + err

        if any(m in combined for m in START_MARKERS) or code == 0:
            messages.append("Đã chạy.")
            client.close()
            return (idx, ip, True, messages)
        if code == 1 and "Session 'pnj' đã chạy" in combined:
            messages.append("Session pnj đã chạy sẵn → OK.")
            client.close()
            return (idx, ip, True, messages)
        if code in (-1, 255) and not combined.strip():
            _, so, _ = client.exec_command("screen -ls | grep -q '\\.pnj\\s' && echo OK || echo NO", timeout=5)
            if so.read().decode().strip() == "OK":
                messages.append("Start exit -1 nhưng screen pnj đang chạy → OK.")
                client.close()
                return (idx, ip, True, messages)
        messages.append(f"Start exit {code}. Output: {combined[:400]}")
        client.close()
        return (idx, ip, False, messages)

    except paramiko.AuthenticationException as e:
        messages.append(f"Lỗi auth: {e}")
        return (idx, ip, False, messages)
    except Exception as e:
        messages.append(f"Lỗi: {e}")
        return (idx, ip, False, messages)


def main():
    parser = argparse.ArgumentParser(
        description="Chỉ update + upload phones + start (không deploy). Cho server đã có ~/pnj_thantai."
    )
    parser.add_argument("-s", "--servers", type=Path, default=DEFAULT_SERVERS_FILE, help="File IP + password")
    parser.add_argument("-n", "--limit", type=int, default=0, help="Chỉ N VPS đầu (0 = tất cả)")
    parser.add_argument("-w", "--workers", type=int, default=50, help="Số VPS đồng thời")
    args = parser.parse_args()
    servers_path = args.servers if args.servers.is_absolute() else DIR / args.servers
    workers = max(1, min(args.workers, 200))

    servers = load_servers(servers_path)
    if not servers:
        print(f"[!] Không có dòng nào trong {servers_path}")
        sys.exit(1)

    n = len(servers)
    if args.limit > 0:
        n = min(n, args.limit)
    tasks = [(i, servers[i][0], servers[i][1]) for i in range(n)]

    print(f"[*] Update + phones + start (không deploy) trên {n} VPS — {servers_path.name}")
    print(f"[*] Số luồng: {min(n, workers)}")
    print()

    ok_count = 0
    done_count = 0
    with ThreadPoolExecutor(max_workers=min(n, workers)) as ex:
        futures = {ex.submit(run_one, t): t for t in tasks}
        for fut in as_completed(futures):
            idx, ip, ok, messages = fut.result()
            done_count += 1
            with print_lock:
                for msg in messages:
                    print(f"[{ip}] {msg}")
                if ok:
                    ok_count += 1
                    print(f"[{ip}] OK")
                else:
                    print(f"[{ip}] THẤT BẠI")
                if done_count % 50 == 0 or done_count == n:
                    print(f"    --- Đã xử lý {done_count}/{n} (OK: {ok_count}) ---")
                print()

    print(f"[*] Xong: {ok_count}/{n} VPS đã update và chạy.")


if __name__ == "__main__":
    main()
