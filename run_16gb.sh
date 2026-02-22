#!/bin/bash
# Chạy 3 workers (ổn định cho 16GB RAM)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate pnj311
cd "$SCRIPT_DIR"
python main.py --workers 5 --headless --continuous --reload-interval 60 "$@"
