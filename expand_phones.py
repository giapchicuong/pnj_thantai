#!/usr/bin/env python3
"""
Tạo file phones với số lượng mong muốn từ danh sách gốc (lặp lại nếu cần).
Dùng: python expand_phones.py [số_lượng_muốn] [file_nguồn] [file_đích]
Ví dụ: python expand_phones.py 200000 phones_all.txt phones_200k.txt
"""
import sys
from pathlib import Path


def main():
    target = int(sys.argv[1]) if len(sys.argv) > 1 else 200_000
    src = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("phones_all.txt")
    out = Path(sys.argv[3]) if len(sys.argv) > 3 else Path("phones_200k.txt")

    lines = [ln.strip() for ln in src.read_text(encoding="utf-8").splitlines() if ln.strip() and not ln.startswith("#")]
    n = len(lines)

    if n == 0:
        print("Lỗi: file nguồn trống.")
        sys.exit(1)

    repeat = (target + n - 1) // n
    result = []
    for _ in range(repeat):
        result.extend(lines)
        if len(result) >= target:
            break

    result = result[:target]
    out.write_text("\n".join(result) + "\n", encoding="utf-8")

    print(f"Đã tạo {out.name}: {len(result):,} SĐT")
    print(f"  Nguồn: {n:,} số duy nhất, lặp {repeat} lần")


if __name__ == "__main__":
    main()
