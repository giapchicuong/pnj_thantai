#!/bin/bash
# Chạy 2 workers (16GB RAM: 3 Chrome dễ OOM → giảm còn 2 ổn định hơn).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONDA_ROOT="${HOME:-/root}/miniconda3"
CONDA_SH="$CONDA_ROOT/etc/profile.d/conda.sh"
if [ ! -f "$CONDA_SH" ]; then
  echo "[!] Không tìm thấy conda: $CONDA_SH"
  exit 1
fi
set -e
source "$CONDA_SH"
conda activate pnj311
cd "$SCRIPT_DIR"
while true; do
  python main.py --workers 2 --headless --continuous --reload-interval 60 "$@"
  code=$?
  echo "[*] main.py thoát (code=$code). Chờ 30s rồi chạy lại..."
  sleep 30
done
