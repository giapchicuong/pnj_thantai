#!/usr/bin/env python3
"""
Tạo 50 file phones từ số 65 tới 114 (phones_65.txt .. phones_114.txt) từ phones_200k, phones_all, phones_aca.
Chia đều số, mỗi số có xác suất đổi 1 chữ số (trừ đầu 0) để trông tự nhiên.
"""
from pathlib import Path
import random

DIR = Path(__file__).parent
PHONES_200K = DIR / "phones_200k.txt"
PHONES_ALL = DIR / "phones_all.txt"
PHONES_ACA = DIR / "phones_aca.txt"
START_NUM = 65
NUM_FILES = 50   # phones_65 .. phones_114
MUTATE_PROB = 0.25


def normalize(s: str) -> str:
    return s.strip()


def mutate_digit(phone: str) -> str:
    """Đổi 1 chữ số ngẫu nhiên (vị trí 1..len-1) thành chữ số khác."""
    if len(phone) < 2:
        return phone
    i = random.randint(1, len(phone) - 1)
    old = phone[i]
    new = old
    while new == old:
        new = str(random.randint(0, 9))
    return phone[:i] + new + phone[i + 1 :]


def main():
    lines = []
    for path in (PHONES_200K, PHONES_ALL, PHONES_ACA):
        if path.exists():
            lines.extend(
                normalize(l) for l in path.read_text(encoding="utf-8").splitlines()
                if normalize(l)
            )

    total = len(lines)
    if total == 0:
        print("Không có dữ liệu từ phones_200k / phones_all / phones_aca.")
        return

    random.shuffle(lines)
    per_file = max(1, total // NUM_FILES)

    for k in range(NUM_FILES):
        file_num = START_NUM + k
        start = k * per_file
        end = total if k == NUM_FILES - 1 else min((k + 1) * per_file, total)
        chunk = lines[start:end]
        out = []
        for p in chunk:
            if not p or not p.isdigit():
                continue
            if random.random() < MUTATE_PROB:
                p = mutate_digit(p)
            out.append(p)
        path = DIR / f"phones_{file_num}.txt"
        path.write_text("\n".join(out) + "\n", encoding="utf-8")
        print(f"  {path.name}: {len(out)} số")

    print(f"Đã tạo xong phones_{START_NUM}.txt .. phones_{START_NUM + NUM_FILES - 1}.txt ({NUM_FILES} file, ~{int(MUTATE_PROB*100)}% số đổi 1 chữ số).")


if __name__ == "__main__":
    main()
