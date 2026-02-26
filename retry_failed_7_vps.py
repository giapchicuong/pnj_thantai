#!/usr/bin/env python3
"""
Chạy lại deploy cho 7 VPS đã thất bại lần trước.
Dùng chung new_servers.txt, new_keys.txt và logic từ deploy_new_7_vps.py.

Chạy: python retry_failed_7_vps.py
"""
from pathlib import Path
import sys

# Import từ deploy script chính
DIR = Path(__file__).parent
sys.path.insert(0, str(DIR))
import deploy_new_7_vps as deploy_mod
from deploy_new_7_vps import (
    load_servers,
    load_keys,
    deploy_one,
    log,
    NEW_SERVERS_FILE,
    NEW_KEYS_FILE,
)

# Retry dùng phones_42, 44, ... nên cần START_PHONE_NUM=1 (tránh dùng 249)
deploy_mod.START_PHONE_NUM = 1

# 7 VPS thất bại (số file phones_N tương ứng)
FAILED_VPS_INDICES = [42, 44, 63, 64, 65, 66, 74]


def main():
    servers = load_servers(NEW_SERVERS_FILE)
    keys = load_keys(NEW_KEYS_FILE)

    n_servers = len(servers)
    n_keys = len(keys)
    if n_servers == 0 or n_keys == 0:
        print(f"[!] Chưa có dữ liệu trong {NEW_SERVERS_FILE} hoặc {NEW_KEYS_FILE}")
        sys.exit(1)

    tasks = []
    for file_idx in FAILED_VPS_INDICES:
        # file_idx = phones_N => server/key ở vị trí (file_idx - 1) (0-based)
        i = file_idx - 1
        if i >= n_servers or i >= n_keys:
            print(f"[!] Bỏ qua VPS {file_idx}: vượt quá số server/keys ({n_servers}/{n_keys})")
            continue
        ip, pwd = servers[i]
        key = keys[i]
        # deploy_one nhận (idx_1based, ip, password, api_key)
        tasks.append((file_idx, ip, pwd, key))

    if not tasks:
        print("[!] Không có VPS nào để retry.")
        sys.exit(1)

    print(f"[*] Retry {len(tasks)} VPS: {FAILED_VPS_INDICES}")
    print()

    ok_count = 0
    for args in tasks:
        idx, ip, ok, messages = deploy_one(args)
        file_idx = idx
        label = f"VPS {file_idx} - {ip}"
        for msg in messages:
            log(label, msg)
        if ok:
            ok_count += 1
        else:
            log(label, "Kết quả: THẤT BẠI")

    print()
    print(f"[*] Xong: {ok_count}/{len(tasks)} VPS retry thành công.")


if __name__ == "__main__":
    main()
