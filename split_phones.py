#!/usr/bin/env python3
"""
Chia phones.txt thành nhiều file cho các instance.
Dùng: python split_phones.py [số_instance] [đường_dẫn_phones.txt]
Ví dụ: python split_phones.py 6 phones.txt
-> Tạo phones_1.txt .. phones_6.txt
"""
import sys
from pathlib import Path


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    src = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("phones.txt")

    lines = [ln.strip() for ln in src.read_text(encoding="utf-8").splitlines() if ln.strip() and not ln.startswith("#")]
    total = len(lines)

    chunk_size = (total + n - 1) // n
    for i in range(n):
        start = i * chunk_size
        end = min(start + chunk_size, total)
        if start >= total:
            break
        out = src.parent / f"phones_{i+1}.txt"
        out.write_text("\n".join(lines[start:end]) + "\n", encoding="utf-8")
        print(f"  {out.name}: {end - start} SĐT (dòng {start+1}-{end})")

    print(f"\nTổng: {total} SĐT chia {n} file. Copy phones_X.txt vào instance tương ứng.")


if __name__ == "__main__":
    main()
