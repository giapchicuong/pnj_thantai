#!/bin/bash
# Chạy 2 workers (16GB RAM: 3 Chrome dễ OOM → giảm còn 2 ổn định hơn).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONDA_ROOT="${HOME:-/root}/miniconda3"
[ ! -d "$CONDA_ROOT" ] && CONDA_ROOT="/root/miniconda3"
PYTHON_BIN="$CONDA_ROOT/envs/pnj311/bin/python"
if [ ! -x "$PYTHON_BIN" ]; then
  CONDA_SH="$CONDA_ROOT/etc/profile.d/conda.sh"
  if [ -f "$CONDA_SH" ]; then
    set +e
    source "$CONDA_SH" && conda activate pnj311
    PYTHON_BIN="$(command -v python)" || PYTHON_BIN=""
  fi
fi
if [ ! -x "$PYTHON_BIN" ]; then
  echo "[!] Không tìm thấy Python (conda pnj311): $CONDA_ROOT"
  exit 1
fi
cd "$SCRIPT_DIR"
while true; do
  "$PYTHON_BIN" main.py --workers 2 --headless --continuous --reload-interval 60 "$@"
  code=$?
  echo "[*] main.py thoát (code=$code). Chờ 30s rồi chạy lại..."
  sleep 30
done
