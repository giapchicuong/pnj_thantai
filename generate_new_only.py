#!/usr/bin/env python3
"""
Tạo SĐT MỚI thuần - không lấy số nào từ nguồn. Chỉ dùng nguồn để phân tích phân phối.
Dùng: python generate_new_only.py [số_lượng] [file_nguồn_1] [file_nguồn_2] ... [file_đích]
"""
import random
import sys
from collections import Counter
from pathlib import Path


def load_lines(path: Path) -> list[str]:
    return [
        ln.strip()
        for ln in path.read_text(encoding="utf-8").splitlines()
        if ln.strip() and not ln.startswith("#")
    ]


def main():
    target = int(sys.argv[1]) if len(sys.argv) > 1 else 200_000
    src_paths = [Path(p) for p in sys.argv[2:-1] if Path(p).exists()]
    out = Path(sys.argv[-1]) if len(sys.argv) > 2 else Path("phones_new.txt")

    if not src_paths:
        src_paths = [Path("phones_all.txt"), Path("phones_200k.txt"), Path("phones_aca.txt")]

    lines = []
    excluded = set()
    for p in src_paths:
        L = load_lines(p)
        lines.extend(L)
        excluded.update(L)

    if not lines:
        print("Lỗi: không có số trong nguồn.")
        sys.exit(1)

    # Phân tích prefix (3 số đầu) từ nguồn
    prefix_counts = Counter(p[:3] for p in lines if len(p) >= 3)
    prefixes = []
    weights = []
    for p, c in prefix_counts.most_common():
        if p.startswith("0") and len(p) == 3:
            prefixes.append(p)
            weights.append(c)

    if not prefixes:
        prefixes = ["098", "099", "097", "093"]
        weights = [400, 300, 200, 100]

    total_w = sum(weights)
    prefix_probs = [w / total_w for w in weights]

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

    result = []
    seen = set(excluded)
    attempts = 0
    max_attempts = target * 30

    print(f"Loại trừ {len(excluded):,} số từ nguồn. Sinh {target:,} số mới...")

    while len(result) < target and attempts < max_attempts:
        num = gen_one()
        if num not in seen and len(num) == 10 and num.startswith("0"):
            seen.add(num)
            result.append(num)
        attempts += 1

    if len(result) < target:
        prefix = prefixes[0]
        while len(result) < target:
            suffix = "".join(random.choices("0123456789", k=7))
            num = prefix + suffix
            if num not in seen:
                seen.add(num)
                result.append(num)

    random.shuffle(result)
    out.write_text("\n".join(result) + "\n", encoding="utf-8")
    print(f"Đã tạo {out.name}: {len(result):,} SĐT mới (không trùng nguồn)")


if __name__ == "__main__":
    main()
