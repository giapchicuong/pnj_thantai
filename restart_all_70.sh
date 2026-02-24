#!/bin/bash
# Restart toàn bộ 70 VPS: STOP -> pull code mới -> START
# Đảm bảo kill process cũ trước khi start (tránh "đã chạy rồi")
# Chạy: bash restart_all_70.sh
#       bash restart_all_70.sh --parallel  (chạy song song, nhanh hơn)

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VPS_FILE="vps_70.txt"
if [ ! -f "$VPS_FILE" ]; then
  echo "[!] Thiếu $VPS_FILE. Tạo file với 70 dòng: IP PASSWORD (mỗi dòng 1 VPS)"
  exit 1
fi

if ! command -v sshpass &>/dev/null; then
  echo "[!] Cài sshpass: sudo apt install sshpass (Ubuntu) hoặc brew install sshpass (Mac)"
  exit 1
fi

PARALLEL=0
[ "$1" = "--parallel" ] || [ "$1" = "-p" ] && PARALLEL=1

SSH_OPTS="-o StrictHostKeyChecking=no -o ConnectTimeout=15 -o ServerAliveInterval=30 -o ServerAliveCountMax=5"

do_one() {
  local i="$1"
  local ip="$2"
  local pass="$3"
  [ -z "$ip" ] || [ -z "$pass" ] && return 1
  echo "[$i/70] $ip - Đang stop + pull + start..."
  sshpass -p "$pass" ssh $SSH_OPTS root@$ip "pkill -f main.py 2>/dev/null; screen -S pnj -X quit 2>/dev/null; sleep 2; cd /root/pnj_thantai 2>/dev/null && git fetch origin main && git reset --hard origin/main && true" 2>/dev/null || true
  [ -f "phones_$i.txt" ] && sshpass -p "$pass" scp $SSH_OPTS "phones_$i.txt" "root@${ip}:/root/pnj_thantai/phones.txt" 2>/dev/null || true
  sshpass -p "$pass" ssh $SSH_OPTS root@$ip "cd /root/pnj_thantai 2>/dev/null && bash start_pnj.sh" 2>/dev/null || true
  echo "[$i/70] $ip - OK"
}

echo "=== Restart 70 VPS (STOP -> git pull -> START) ==="
echo ""

i=0
while IFS= read -r line; do
  [[ "$line" =~ ^# ]] && continue
  ip=$(echo "$line" | awk '{print $1}')
  pass=$(echo "$line" | awk '{print $2}')
  [ -z "$ip" ] && continue
  i=$((i + 1))
  if [ "$PARALLEL" = "1" ]; then
    do_one "$i" "$ip" "$pass" &
  else
    do_one "$i" "$ip" "$pass"
  fi
done < "$VPS_FILE"

[ "$PARALLEL" = "1" ] && wait

echo ""
echo "=== Xong ==="
