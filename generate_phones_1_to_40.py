#!/usr/bin/env python3
"""
Tạo phones_1.txt .. phones_40.txt từ phones_200k.txt và phones_aca.txt.
Chia đều số, mỗi số có xác suất đổi 1 chữ số (trừ đầu 0) để trông tự nhiên hơn.
"""
from pathlib import Path
import random

DIR = Path(__file__).parent
PHONES_200K = DIR / "phones_200k.txt"
PHONES_ACA = DIR / "phones_aca.txt"
NUM_FILES = 40
# Xác suất đổi 1 chữ số ngẫu nhiên trong mỗi số (0 = giữ nguyên)
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
    lines_200k = []
    if PHONES_200K.exists():
        lines_200k = [normalize(l) for l in PHONES_200K.read_text(encoding="utf-8").splitlines() if normalize(l)]
    lines_aca = []
    if PHONES_ACA.exists():
        lines_aca = [normalize(l) for l in PHONES_ACA.read_text(encoding="utf-8").splitlines() if normalize(l)]

    total = len(lines_200k) + len(lines_aca)
    if total == 0:
        print("Không có dữ liệu từ phones_200k.txt / phones_aca.txt.")
        return

    # Chia đều: file i nhận chunk thứ i
    per_file = max(1, total // NUM_FILES)
    combined = lines_200k + lines_aca
    random.shuffle(combined)

    for i in range(1, NUM_FILES + 1):
        start = (i - 1) * per_file
        end = total if i == NUM_FILES else min((i) * per_file, total)
        chunk = combined[start:end]
        out = []
        for p in chunk:
            if not p or not p.isdigit():
                continue
            if random.random() < MUTATE_PROB:
                p = mutate_digit(p)
            out.append(p)
        path = DIR / f"phones_{i}.txt"
        path.write_text("\n".join(out) + "\n", encoding="utf-8")
        print(f"  {path.name}: {len(out)} số")

    print(f"Đã tạo xong phones_1.txt .. phones_{NUM_FILES}.txt (mỗi số có ~{int(MUTATE_PROB*100)}% đổi 1 chữ số).")


if __name__ == "__main__":
    main()
