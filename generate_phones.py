#!/usr/bin/env python3
"""
Tạo SĐT mới từ mẫu có sẵn - random theo phân phối prefix & digit (số trông như thật).
Dùng: python generate_phones.py [số_lượng] [file_nguồn] [file_đích]
Ví dụ: python generate_phones.py 200000 phones_all.txt phones_200k.txt
"""
import random
import sys
from collections import Counter
from pathlib import Path


def main():
    target = int(sys.argv[1]) if len(sys.argv) > 1 else 200_000
    src = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("phones_all.txt")
    out = Path(sys.argv[3]) if len(sys.argv) > 3 else Path("phones_200k.txt")

    lines = [
        ln.strip()
        for ln in src.read_text(encoding="utf-8").splitlines()
        if ln.strip() and not ln.startswith("#")
    ]
    existing = set(lines)
    n = len(existing)

    if n == 0:
        print("Lỗi: file nguồn trống.")
        sys.exit(1)

    # Phân tích prefix (3 số đầu)
    prefix_counts = Counter(p[:3] for p in lines if len(p) >= 3)
    prefixes = []
    weights = []
    for p, c in prefix_counts.most_common():
        if p.startswith("0") and len(p) == 3:  # 098, 099, 086...
            prefixes.append(p)
            weights.append(c)

    if not prefixes:
        prefixes = ["098", "099"]
        weights = [980, 20]

    total_w = sum(weights)
    prefix_probs = [w / total_w for w in weights]

    # Phân tích xác suất digit ở mỗi vị trí (4-9, mỗi vị trí 1 digit)
    positions = {}
    for pos in range(4, 10):
        counts = Counter()
        for p in lines:
            if len(p) > pos and p[:3] in prefixes:
                counts[p[pos]] += 1
        if counts:
            total = sum(counts.values())
            positions[pos] = [(d, c / total) for d, c in counts.most_common()]
        else:
            positions[pos] = [(str(i), 0.1) for i in range(10)]

    def gen_one():
        prefix = random.choices(prefixes, weights=prefix_probs)[0]
        suffix = ""
        for pos in range(4, 10):
            dig_probs = positions.get(pos, [(str(i), 0.1) for i in range(10)])
            digits, probs = zip(*dig_probs) if dig_probs else (tuple("0123456789"), (0.1,) * 10)
            suffix += random.choices(digits, weights=probs)[0]
        return prefix + suffix

    result = list(existing)  # Giữ nguyên 50k số thật
    need = target - len(result)
    seen = set(result)
    attempts = 0
    max_attempts = need * 20  # Tránh loop vô hạn

    print(f"Nguồn: {n:,} số. Cần thêm {need:,} số mới (phân phối từ mẫu)...")

    while len(result) < target and attempts < max_attempts:
        num = gen_one()
        if num not in seen and len(num) == 10 and num.startswith("0"):
            seen.add(num)
            result.append(num)
        attempts += 1

    if len(result) < target:
        # Fallback: random thuần cho phần còn thiếu
        prefix = prefixes[0]
        while len(result) < target:
            suffix = "".join(random.choices("0123456789", k=7))
            num = prefix + suffix
            if num not in seen:
                seen.add(num)
                result.append(num)

    random.shuffle(result)
    out.write_text("\n".join(result) + "\n", encoding="utf-8")
    print(f"Đã tạo {out.name}: {len(result):,} SĐT ({n:,} gốc + {len(result)-n:,} sinh)")


if __name__ == "__main__":
    main()
