#!/bin/bash
# Chạy tool mục tiêu 500k lượt: 2 workers, không headless, continuous
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
bash "$SCRIPT_DIR/run.sh" --workers 6 --continuous --reload-interval 60 "$@"
