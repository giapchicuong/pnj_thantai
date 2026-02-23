#!/bin/bash
# Chạy 1 worker (ổn định nhất - tránh Chrome crash)
# Dùng xvfb-run nếu có (tránh Chrome crash trên server không có display)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate pnj311
cd "$SCRIPT_DIR"
if command -v xvfb-run &>/dev/null; then
  xvfb-run -a -s "-screen 0 1920x1080x24 +extension GLX" python -u main.py --workers 1 --headless --continuous --reload-interval 60 "$@"
else
  python -u main.py --workers 1 --headless --continuous --reload-interval 60 "$@"
fi
