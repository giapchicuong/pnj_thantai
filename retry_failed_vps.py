#!/usr/bin/env python3
"""
Chạy lại deploy cho các VPS đã lỗi (dùng chung new_servers.txt, new_keys.txt).
Retry liên tục đến khi tất cả thành công.
Dùng cùng START_PHONE_NUM với deploy_new_7_vps (48 → phones_48..87).
"""
from pathlib import Path
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from deploy_new_7_vps import (
    deploy_one,
    load_servers,
    load_keys,
    log,
    NEW_SERVERS_FILE,
    NEW_KEYS_FILE,
    START_PHONE_NUM,
)

DIR = Path(__file__).parent
RETRY_LIST_FILE = DIR / "retry_list.txt"
RETRY_DELAY_SEC = 3


def load_retry_list(path: Path) -> list[int]:
    """Đọc danh sách số VPS (48–87 tương ứng phones_48..87), mỗi dòng 1 số."""
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").strip().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            n = int(line)
            if START_PHONE_NUM <= n <= 127 and n not in out:
                out.append(n)
        except ValueError:
            continue
    return sorted(out)


def main():
    vps_numbers = load_retry_list(RETRY_LIST_FILE)
    if not vps_numbers:
        print(f"[!] Chưa có số VPS trong {RETRY_LIST_FILE}")
        print(f"    Mỗi dòng 1 số từ {START_PHONE_NUM} trở đi (ví dụ: 48, 50, 87)")
        sys.exit(1)

    servers = load_servers(NEW_SERVERS_FILE)
    keys = load_keys(NEW_KEYS_FILE)
    n_max = min(len(servers), len(keys))
    if n_max == 0:
        print("[!] Chưa có dữ liệu trong new_servers.txt hoặc new_keys.txt")
        sys.exit(1)

    tasks = []
    for vps_num in vps_numbers:
        idx = vps_num - START_PHONE_NUM + 1  # 48 -> 1, 87 -> 40
        if idx < 1 or idx > n_max:
            print(f"[!] Bỏ qua {vps_num}: nằm ngoài phạm vi (1–{n_max} tương ứng phones_{START_PHONE_NUM}..{START_PHONE_NUM + n_max - 1})")
            continue
        ip, pwd = servers[idx - 1]
        key = keys[idx - 1]
        tasks.append((idx, ip, pwd, key))

    if not tasks:
        print("[!] Không có VPS hợp lệ trong retry_list.txt")
        sys.exit(1)

    round_num = 0
    while tasks:
        round_num += 1
        if round_num > 1:
            print()
            time.sleep(RETRY_DELAY_SEC)
        labels = [f"VPS {40 + t[0]} - {t[1]}" for t in tasks]
        print(f"[*] Đang thử lại {len(tasks)} VPS lỗi (vòng {round_num}): {', '.join(labels)}")
        print()

        failed = []
        with ThreadPoolExecutor(max_workers=len(tasks)) as ex:
            futures = {ex.submit(deploy_one, t): t for t in tasks}
            for fut in as_completed(futures):
                idx, ip, ok, messages = fut.result()
                label = f"VPS {START_PHONE_NUM + idx - 1} - {ip}"
                for msg in messages:
                    log(label, msg)
                if ok:
                    log(label, "Thử lại: thành công.")
                else:
                    log(label, "Kết quả: THẤT BẠI (sẽ thử lại)")
                    failed.append((idx, ip, servers[idx - 1][1], keys[idx - 1]))
        tasks = failed

    print()
    print("[*] Tất cả VPS đã thành công.")


if __name__ == "__main__":
    main()
