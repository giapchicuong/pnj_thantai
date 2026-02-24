#!/bin/bash
# 1. Push code lên Git
# 2. Restart 70 VPS (stop -> pull mới -> start)
# Chạy: bash deploy_and_restart_70.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Bước 1: Push code lên Git ==="
git add -A
git status
COMMIT_MSG="${1:-Update code}"
git commit -m "$COMMIT_MSG" 2>/dev/null || { echo "[*] Không có thay đổi hoặc đã commit"; }
git push origin main
echo ""

echo "=== Bước 2: Restart 70 VPS ==="
bash restart_all_70.sh "${@:2}"
