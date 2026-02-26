#!/usr/bin/env python3
"""
Tạo phones_1.txt .. phones_300.txt từ phones_aca.txt, phones_all.txt, phones_200k.txt.
Mỗi file ~10.000 số. Random đổi 1 hoặc 2 chữ số (trừ đầu 0) để trông tự nhiên.
Nếu tổng nguồn < 3M số thì sẽ nhân bản + mutate để đủ 300 x 10k.
"""
from pathlib import Path
import random

DIR = Path(__file__).parent
SOURCES = [
    DIR / "phones_200k.txt",
    DIR / "phones_all.txt",
    DIR / "phones_aca.txt",
]
START_NUM = 1
NUM_FILES = 300
TARGET_PER_FILE = 10_000
TOTAL_NEEDED = NUM_FILES * TARGET_PER_FILE  # 3_000_000

# Xác suất đổi 1 chữ số / 2 chữ số (số còn lại giữ nguyên)
MUTATE_ONE_PROB = 0.30
MUTATE_TWO_PROB = 0.15


def normalize(s: str) -> str:
    return s.strip()


def mutate_digits(phone: str, count: int) -> str:
    """Đổi `count` chữ số ngẫu nhiên (vị trí 1..len-1) thành chữ số khác."""
    if len(phone) < 2 or count < 1:
        return phone
    indices = list(range(1, len(phone)))
    if count > len(indices):
        count = len(indices)
    chosen = random.sample(indices, count)
    arr = list(phone)
    for i in chosen:
        old = arr[i]
        new = old
        while new == old:
            new = str(random.randint(0, 9))
        arr[i] = new
    return "".join(arr)


def main():
    lines = []
    for path in SOURCES:
        if path.exists():
            n = 0
            for line in path.read_text(encoding="utf-8").splitlines():
                s = normalize(line)
                if s and s.isdigit() and len(s) >= 10:
                    lines.append(s)
                    n += 1
            print(f"  {path.name}: {n} số")
        else:
            print(f"  {path.name}: (không tìm thấy, bỏ qua)")

    if not lines:
        print("Không có dữ liệu từ bất kỳ file nguồn nào.")
        return

    random.shuffle(lines)
    total = len(lines)

    # Nếu chưa đủ 3M thì nhân bản + mutate để đủ (tránh trùng lặp)
    if total < TOTAL_NEEDED:
        print(f"Tổng nguồn: {total}. Cần {TOTAL_NEEDED}. Đang nhân bản + mutate...")
        expanded = list(lines)
        while len(expanded) < TOTAL_NEEDED:
            take = min(len(lines), TOTAL_NEEDED - len(expanded))
            sample = random.choices(lines, k=take)
            for p in sample:
                r = random.random()
                if r < MUTATE_TWO_PROB:
                    p = mutate_digits(p, 2)
                elif r < MUTATE_TWO_PROB + MUTATE_ONE_PROB:
                    p = mutate_digits(p, 1)
                expanded.append(p)
        random.shuffle(expanded)
        lines = expanded
        total = len(lines)
        print(f"Sau khi nhân bản: {total} số.")
    else:
        lines = lines[:TOTAL_NEEDED]
        total = len(lines)

    per_file = total // NUM_FILES
    remainder = total % NUM_FILES

    for k in range(NUM_FILES):
        file_num = START_NUM + k
        start = k * per_file + min(k, remainder)
        end = start + per_file + (1 if k < remainder else 0)
        chunk = lines[start:end]

        out = []
        for p in chunk:
            if not p or not p.isdigit():
                continue
            r = random.random()
            if r < MUTATE_TWO_PROB:
                p = mutate_digits(p, 2)
            elif r < MUTATE_TWO_PROB + MUTATE_ONE_PROB:
                p = mutate_digits(p, 1)
            out.append(p)

        path = DIR / f"phones_{file_num}.txt"
        path.write_text("\n".join(out) + "\n", encoding="utf-8")
        if (k + 1) % 50 == 0 or k == 0 or k == NUM_FILES - 1:
            print(f"  {path.name}: {len(out)} số")

    print(f"\nĐã tạo xong phones_{START_NUM}.txt .. phones_{START_NUM + NUM_FILES - 1}.txt ({NUM_FILES} file).")
    print(f"Mỗi file ~{TARGET_PER_FILE} số. ~{int(MUTATE_ONE_PROB*100)}% đổi 1 chữ số, ~{int(MUTATE_TWO_PROB*100)}% đổi 2 chữ số.")


if __name__ == "__main__":
    main()
