#!/bin/bash
# Chạy 6 workers (test - tăng từ 3)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate pnj311
cd "$SCRIPT_DIR"
python main.py --workers 8 --headless --continuous --reload-interval 60 "$@"
