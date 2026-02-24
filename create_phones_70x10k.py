#!/usr/bin/env python3
"""
Tạo 70 file phones_1.txt .. phones_70.txt, mỗi file 10.000 SĐT.
SĐT random prefix VN (098, 099, 090, 093...) + 7 số.
Chạy: python3 create_phones_70x10k.py
"""
import random
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PREFIXES = ["098", "099", "090", "093", "089", "088", "091", "094", "086", "084", "085", "079", "077", "076", "078", "070", "056", "058"]
TOTAL = 700_000  # 70 × 10_000
PER_FILE = 10_000
N_FILES = 70


def main():
    print(f"[*] Tạo {TOTAL:,} SĐT, chia {N_FILES} file × {PER_FILE:,} số...")
    seen = set()
    result = []
    attempts = 0
    max_attempts = TOTAL * 15

    while len(result) < TOTAL and attempts < max_attempts:
        prefix = random.choice(PREFIXES)
        suffix = "".join(random.choices("0123456789", k=7))
        num = prefix + suffix
        if num not in seen:
            seen.add(num)
            result.append(num)
        attempts += 1

    if len(result) < TOTAL:
        # Fallback: thêm số còn thiếu
        while len(result) < TOTAL:
            p = random.choice(PREFIXES)
            s = "".join(random.choices("0123456789", k=7))
            n = p + s
            if n not in seen:
                seen.add(n)
                result.append(n)

    random.shuffle(result)
    print(f"[*] Đã tạo {len(result):,} SĐT duy nhất.")

    for i in range(N_FILES):
        start = i * PER_FILE
        end = min(start + PER_FILE, len(result))
        chunk = result[start:end]
        out = SCRIPT_DIR / f"phones_{i+1}.txt"
        out.write_text("\n".join(chunk) + "\n", encoding="utf-8")
        print(f"  phones_{i+1}.txt: {len(chunk):,} SĐT")

    print(f"\n[*] Xong. Chạy restart 70 VPS với số mới:")
    print(f"    python3 import_excel_and_run.py /Users/giapchicuong/Desktop/3829864_260223155302.xlsx")
    print(f"    (hoặc: bash check_and_fix_1_70.sh --all)")


if __name__ == "__main__":
    main()
