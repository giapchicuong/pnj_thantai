#!/usr/bin/env python3
"""
Chia phones.txt thành nhiều file cho các instance.
Dùng: python split_phones.py [số_instance] [đường_dẫn_phones.txt] [bắt_đầu_từ]
Ví dụ: python split_phones.py 6 phones.txt
  -> Tạo phones_1.txt .. phones_6.txt
Ví dụ: python split_phones.py 27 phones_200k.txt 9
  -> Tạo phones_9.txt .. phones_35.txt (27 file)
"""
import sys
from pathlib import Path


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    src = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("phones.txt")
    start_at = int(sys.argv[3]) if len(sys.argv) > 3 else 1

    lines = [ln.strip() for ln in src.read_text(encoding="utf-8").splitlines() if ln.strip() and not ln.startswith("#")]
    total = len(lines)

    chunk_size = (total + n - 1) // n
    for i in range(n):
        start = i * chunk_size
        end = min(start + chunk_size, total)
        if start >= total:
            break
        file_num = start_at + i
        out = src.parent / f"phones_{file_num}.txt"
        out.write_text("\n".join(lines[start:end]) + "\n", encoding="utf-8")
        print(f"  {out.name}: {end - start} SĐT (dòng {start+1}-{end})")

    last = start_at + n - 1
    print(f"\nTổng: {total} SĐT chia {n} file -> phones_{start_at}.txt .. phones_{last}.txt")


if __name__ == "__main__":
    main()
