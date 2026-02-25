#!/usr/bin/env python3
"""
Đọc file vps_ip_pass.xlsx (6 VPS đầu: cột STT, IP, User, Password, API_KEY)
và in ra lệnh để trên mỗi VPS: git pull (lấy code mới nhất) rồi chạy tool với đúng API key.
Như vậy khi bạn push code, mỗi VPS chỉ cần git pull là không bị overwrite config (key đặt bằng env).
"""
from pathlib import Path
import openpyxl

SHEET_NAME = "vps_ip_pass.xlsx"
MAX_VPS = 6  # Chỉ xử lý 6 con đầu
REPO_DIR_DEFAULT = "pnj_thantai"  # Thư mục repo trên VPS (sửa nếu bạn đặt khác)


def main():
    path = Path(__file__).parent / SHEET_NAME
    if not path.exists():
        print(f"Chưa có file {SHEET_NAME}. Chạy: python create_vps_sheet.py")
        return
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(min_row=2, max_row=1 + MAX_VPS, values_only=True))
    wb.close()

    repo = REPO_DIR_DEFAULT
    print("=" * 60)
    print("LỆNH CHO TỪNG VPS (1–6) — copy từng block, thay <IP_N> rồi chạy")
    print("=" * 60)

    for row in rows:
        if not row or row[0] is None:
            continue
        stt = row[0]
        ip = (row[1] or "").strip() if len(row) > 1 else ""
        user = (row[2] or "root").strip() if len(row) > 2 else "root"
        api_key = (row[4] or "").strip() if len(row) > 4 else ""
        if not api_key:
            continue
        ip_placeholder = ip if ip else f"<IP_{int(stt)}>"
        print(f"\n--- VPS {int(stt)} ---")
        print(f"# Bước 1: SSH vào VPS")
        print(f"ssh {user}@{ip_placeholder}")
        print()
        print(f"# Bước 2: Trên VPS — copy cả block dán vào terminal")
        print(f"cd ~/{repo}")
        print(f"git fetch origin")
        print(f"git reset --hard origin/main")
        print(f"screen -S pnj -X quit 2>/dev/null || true")
        print(f"export TMPROXY_API_KEY={api_key}")
        print(f"cd ~/{repo} && bash start_pnj.sh")
        print()

    print("=" * 60)
    print("Lưu ý: export TMPROXY_API_KEY đặt trước start_pnj.sh để session screen dùng đúng key.")
    print("=" * 60)


if __name__ == "__main__":
    main()
