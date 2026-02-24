#!/usr/bin/env python3
"""
Đọc IP + mật khẩu từ file Excel (sadsad.xlsx), cập nhật vào các script:
  fix_config_and_start_30_vps.sh, setup_30_vps.sh, check_30_vps.sh, start_pnj_30_vps.sh
Cột: IPv4 (D), Password (F). Hàng 2–31 = STT 1–30.

Cách dùng:
  python3 update_vps_credentials_from_excel.py
  python3 update_vps_credentials_from_excel.py /path/to/sadsad.xlsx
"""
import re
import sys
from pathlib import Path

try:
    import openpyxl
except ImportError:
    print("Cần openpyxl: pip install openpyxl")
    sys.exit(1)

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_XLSX = Path.home() / "Desktop" / "sadsad.xlsx"
TARGETS = [
    "fix_config_and_start_30_vps.sh",
    "setup_30_vps.sh",
    "check_30_vps.sh",
    "start_pnj_30_vps.sh",
]


def read_excel(path):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    ips, passs = [], []
    for row in ws.iter_rows(min_row=2, max_row=31, min_col=4, max_col=6, values_only=True):
        if row[0] is not None and row[2] is not None:  # IPv4, Password
            ips.append(str(row[0]).strip())
            passs.append(str(row[2]).strip())
    wb.close()
    return ips, passs


def format_bash_arrays(ips, passs):
    # IPS: 5+5+5+5+5+5
    ips_lines = [
        "  " + " ".join(ips[0:5]),
        "  " + " ".join(ips[5:10]),
        "  " + " ".join(ips[10:15]),
        "  " + " ".join(ips[15:20]),
        "  " + " ".join(ips[20:25]),
        "  " + " ".join(ips[25:30]),
    ]
    pass_lines = []
    for i in range(0, 30, 5):
        chunk = ["'" + p + "'" for p in passs[i : i + 5]]
        pass_lines.append("  " + "   ".join(chunk))
    return "\n".join(ips_lines), "\n".join(pass_lines)


def main():
    xlsx = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_XLSX
    if not xlsx.exists():
        print(f"Không tìm thấy: {xlsx}")
        sys.exit(1)
    ips, passs = read_excel(xlsx)
    if len(ips) != 30 or len(passs) != 30:
        print(f"Excel cần đủ 30 dòng (STT 1–30). Hiện: {len(ips)} IP, {len(passs)} pass.")
        sys.exit(1)
    ips_block, pass_block = format_bash_arrays(ips, passs)
    comment = "# IP + pass lấy từ sadsad.xlsx (cột IPv4, Password) — cập nhật: python3 update_vps_credentials_from_excel.py\n"
    ips_declare = "declare -a IPS=(\n" + ips_block + "\n)"
    pass_declare = "declare -a PASS=(\n" + pass_block + "\n)"

    # Pattern: optional comment line then declare -a IPS= ... declare -a PASS= ...
    pattern = re.compile(
        r"(# IP.*sadsad.*\n)?(declare -a IPS=\(\s*\n.*?\n\)\s*\n)(declare -a PASS=\(\s*\n.*?\n\)\s*\n)",
        re.DOTALL,
    )
    replacement = comment + ips_declare + "\n" + pass_declare + "\n"

    updated = 0
    for name in TARGETS:
        path = SCRIPT_DIR / name
        if not path.exists():
            print(f"Bỏ qua (không có file): {path}")
            continue
        text = path.read_text(encoding="utf-8")
        new_text = pattern.sub(replacement, text, count=1)
        if new_text == text:
            # Fallback: không có comment, chỉ thay block IPS...PASS
            pattern_no_comment = re.compile(
                r"declare -a IPS=\(\s*\n.*?\n\)\s*\ndeclare -a PASS=\(\s*\n.*?\n\)\s*\n",
                re.DOTALL,
            )
            new_text = pattern_no_comment.sub(comment + ips_declare + "\n" + pass_declare + "\n", text, count=1)
        if new_text != text:
            path.write_text(new_text, encoding="utf-8")
            print(f"Đã cập nhật: {name}")
            updated += 1
        else:
            print(f"Không đổi: {name}")
    print(f"Xong. Đã sửa {updated}/{len(TARGETS)} file.")


if __name__ == "__main__":
    main()
