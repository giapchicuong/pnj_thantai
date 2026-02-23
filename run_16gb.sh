#!/bin/bash
# Chạy 4 workers (toàn bộ VPS 1-70, 16GB RAM)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate pnj311
cd "$SCRIPT_DIR"
python -u main.py --workers 4 --headless --continuous --reload-interval 60 "$@"
