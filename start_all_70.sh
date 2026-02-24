#!/bin/bash
# Chạy tuần tự qua 70 VPS: chỉ khởi động start_pnj.sh
# Dùng: bash start_all_70.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VPS_FILE="vps_70.txt"
if [ ! -f "$VPS_FILE" ]; then
  echo "[!] Thiếu $VPS_FILE. Mỗi dòng: IP PASSWORD"
  exit 1
fi

if ! command -v sshpass &>/dev/null; then
  echo "[!] Cài sshpass: brew install sshpass (Mac) hoặc sudo apt install sshpass (Ubuntu)"
  exit 1
fi

SSH_OPTS="-T -o StrictHostKeyChecking=no -o ConnectTimeout=30 -o ServerAliveInterval=30 -o ServerAliveCountMax=5"

echo "=== Khởi động 70 VPS: start_pnj.sh (tuần tự) ==="
echo ""

i=0
exec 9< "$VPS_FILE"
while IFS= read -r line <&9; do
  [[ "$line" =~ ^# ]] && continue
  [[ -z "$line" ]] && continue
  ip=$(echo "$line" | awk '{print $1}')
  pass=$(echo "$line" | awk '{print $2}')
  [[ -z "$ip" || -z "$pass" ]] && continue
  i=$((i + 1))
  echo "[$i/70] $ip - start_pnj.sh..."
  sshpass -p "$pass" ssh $SSH_OPTS root@$ip "cd ~/pnj_thantai && bash start_pnj.sh" < /dev/null 2>/dev/null || true
  echo "[$i/70] $ip - OK"
done
exec 9<&-

echo ""
echo "=== Xong 70 VPS ==="
