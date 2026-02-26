#!/bin/bash
# Chạy 6 workers (--workers 6)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate pnj311
cd "$SCRIPT_DIR"
python main.py --workers 1 --headless --continuous --reload-interval 60 "$@"
