#!/usr/bin/env python3
"""
Deploy (nếu chưa có thư mục) + update + start. Dùng cho VPS MỚI / chưa có ~/pnj_thantai.
Chạy update_and_run_all.py trước cho server ĐÃ CHẠY; script này cho server còn lại.

Đầu vào: all_vps.txt (IP<Tab>Password). phones_1.txt, phones_2.txt... → VPS 1, 2, ...
Trên mỗi VPS: (1) Deploy nếu chưa có thư mục (2) git pull (3) upload phones (4) kill + start_pnj.sh

  python deploy_and_run_all.py
  python deploy_and_run_all.py -s all_vps.txt -w 50 -n 200
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
CMD_TIMEOUT = 900   # deploy có thể lâu
DEPLOY_SUCCESS_MARKER = "=== Deploy xong ==="  # deploy_vps.sh in ra khi chạy xong
MAX_DEPLOY_ATTEMPTS = 3
DEPLOY_RETRY_DELAY = 10
# Khi thấy một trong các dòng này trong output start_pnj.sh → coi là đã chạy
START_MARKERS = (
    "[*] Khởi động PNJ trong screen",   # start_pnj.sh vừa mở screen
    "[!] Session 'pnj' đã chạy",       # session đã có sẵn (start_pnj.sh exit 1)
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
    label = f"{ip}"
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

        # 1. Check có thư mục pnj_thantai chưa
        stdin, stdout, stderr = client.exec_command(
            "test -d /root/pnj_thantai && echo YES || echo NO",
            timeout=10,
        )
        has_dir = (stdout.read().decode().strip() == "YES")
        if not has_dir:
            local_deploy = DIR / "deploy_vps.sh"
            use_local_deploy = local_deploy.is_file()
            if use_local_deploy:
                messages.append("Chưa có thư mục → deploy bằng file local deploy_vps.sh")
            else:
                messages.append("Chưa có thư mục → đang deploy (curl deploy_vps.sh | bash)...")
            deploy_ok = False
            for attempt in range(1, MAX_DEPLOY_ATTEMPTS + 1):
                if use_local_deploy:
                    sftp = client.open_sftp()
                    sftp.put(str(local_deploy), "/tmp/deploy_vps.sh")
                    sftp.close()
                    stdin, stdout, stderr = client.exec_command(
                        "bash /tmp/deploy_vps.sh",
                        timeout=CMD_TIMEOUT,
                    )
                else:
                    stdin, stdout, stderr = client.exec_command(
                        "curl -sL https://raw.githubusercontent.com/giapchicuong/pnj_thantai/main/deploy_vps.sh | bash",
                        timeout=CMD_TIMEOUT,
                    )
                out = stdout.read().decode("utf-8", errors="replace")
                err = stderr.read().decode("utf-8", errors="replace")
                code = stdout.channel.recv_exit_status()
                combined = out + "\n" + err
                if code == 0 and DEPLOY_SUCCESS_MARKER in combined:
                    deploy_ok = True
                    messages.append(f"Deploy xong (lần {attempt}).")
                    break
                if attempt < MAX_DEPLOY_ATTEMPTS:
                    messages.append(f"Deploy chưa thấy '{DEPLOY_SUCCESS_MARKER}' (lần {attempt}), thử lại sau {DEPLOY_RETRY_DELAY}s...")
                    time.sleep(DEPLOY_RETRY_DELAY)
            if not deploy_ok:
                # Nếu script deploy thoát giữa chừng nhưng đã tạo được thư mục + repo thì vẫn tiếp tục
                stdin, stdout, stderr = client.exec_command(
                    "test -f /root/pnj_thantai/main.py && echo YES || echo NO",
                    timeout=10,
                )
                has_repo = (stdout.read().decode().strip() == "YES")
                if has_repo:
                    messages.append(f"Deploy chưa in xong marker nhưng đã có repo → tiếp tục git pull + start.")
                else:
                    messages.append(f"Deploy thất bại sau {MAX_DEPLOY_ATTEMPTS} lần. Output: {(out + err)[:400]}")
                    client.close()
                    return (idx, ip, False, messages)
        else:
            messages.append("Đã có thư mục → bỏ qua deploy.")

        # 2. Update code
        messages.append("Đang git pull...")
        stdin, stdout, stderr = client.exec_command(
            "cd /root/pnj_thantai && git fetch origin && git reset --hard origin/main",
            timeout=120,
        )
        stdout.channel.recv_exit_status()
        out = stdout.read().decode("utf-8", errors="replace")
        err = stderr.read().decode("utf-8", errors="replace")
        code = stdout.channel.recv_exit_status()
        if code != 0:
            messages.append(f"Git lỗi (exit {code}): {(err or out)[:200]}")
        else:
            messages.append("Git xong.")

        # 2.5. Upload phones_{số}.txt → ~/pnj_thantai/phones.txt (VPS 1 = phones_1.txt, VPS 40 = phones_40.txt, ...)
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
            messages.append(f"Không có file phones_{file_idx}.txt → bỏ qua upload")

        # 3. Kill session/process cũ rồi mới start
        messages.append("Đang start_pnj.sh...")
        kill_cmd = (
            "screen -S pnj -X quit 2>/dev/null || true; "
            "pkill -f 'run_16gb.sh|start_pnj.sh|main.py.*pnj' 2>/dev/null || true"
        )
        _, so_kill, _ = client.exec_command(kill_cmd, timeout=15)
        so_kill.channel.recv_exit_status()
        time.sleep(1)  # Đợi process cũ thoát hẳn

        # Chạy start_pnj.sh trong PTY để có exit code + output đúng (tránh exit -1)
        stdin, stdout, stderr = client.exec_command(
            "cd /root/pnj_thantai && bash start_pnj.sh",
            timeout=30,
            get_pty=True,
        )
        out = stdout.read().decode("utf-8", errors="replace")
        err = stderr.read().decode("utf-8", errors="replace")
        code = stdout.channel.recv_exit_status()
        combined = out + "\n" + err

        started = any(m in combined for m in START_MARKERS)
        if started or code == 0:
            messages.append("Đã chạy (thấy log Khởi động PNJ / Session pnj).")
            client.close()
            return (idx, ip, True, messages)
        if code == 1 and "Session 'pnj' đã chạy" in combined:
            messages.append("Session pnj đã chạy sẵn → OK.")
            client.close()
            return (idx, ip, True, messages)
        # Exit -1 hoặc output rỗng: có thể screen đã chạy (channel đóng sớm). Kiểm tra screen -ls
        if code in (-1, 255) and not combined.strip():
            _, so, _ = client.exec_command("screen -ls | grep -q '\\.pnj\\s' && echo OK || echo NO", timeout=5)
            check = so.read().decode().strip()
            if check == "OK":
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
        description="Deploy (nếu chưa có) + update + start PNJ trên tất cả VPS (đọc all_vps.txt)"
    )
    parser.add_argument(
        "-s", "--servers",
        type=Path,
        default=DEFAULT_SERVERS_FILE,
        help=f"File IP + password (mặc định: {DEFAULT_SERVERS_FILE.name})",
    )
    parser.add_argument(
        "-n", "--limit",
        type=int,
        default=0,
        help="Chỉ xử lý N VPS đầu (0 = tất cả)",
    )
    parser.add_argument(
        "-w", "--workers",
        type=int,
        default=50,
        help="Số VPS xử lý đồng thời (mặc định: 50)",
    )
    args = parser.parse_args()
    servers_path = args.servers if args.servers.is_absolute() else DIR / args.servers
    workers = max(1, min(args.workers, 200))  # 500 VPS: nên dùng -w 80 ~ 100

    servers = load_servers(servers_path)
    if not servers:
        print(f"[!] Không có dòng nào trong {servers_path}")
        print("    Định dạng: mỗi dòng  IP<Tab>Password")
        sys.exit(1)

    n = len(servers)
    if args.limit > 0:
        n = min(n, args.limit)
    tasks = [(i, servers[i][0], servers[i][1]) for i in range(n)]

    num_workers = min(n, workers)
    print(f"[*] Deploy (nếu chưa có) + update + start trên {n} VPS (file: {servers_path.name})")
    print(f"[*] Số luồng đồng thời: {num_workers}")
    print()

    ok_count = 0
    done_count = 0
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
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
                    print(f"    --- Đã xử lý {done_count}/{n} VPS (OK: {ok_count}) ---")
                print()

    print(f"[*] Xong: {ok_count}/{n} VPS đã deploy/update và chạy.")


if __name__ == "__main__":
    main()
