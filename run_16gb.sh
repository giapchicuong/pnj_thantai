#!/bin/bash
# Chạy 8 workers. Vòng lặp: nếu main.py thoát (crash/exception) thì chờ 30s rồi chạy lại → screen luôn có process.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate pnj311
cd "$SCRIPT_DIR"
while true; do
  python main.py --workers 2 --headless --continuous --reload-interval 60 "$@"
  code=$?
  echo "[*] main.py thoát (code=$code). Chờ 30s rồi chạy lại..."
  sleep 30
done
