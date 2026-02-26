#!/bin/bash
# Chạy 3 workers (không proxy)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate pnj311
cd "$SCRIPT_DIR"
python main.py --workers 3 --headless --continuous --reload-interval 60 "$@"
