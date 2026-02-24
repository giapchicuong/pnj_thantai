#!/bin/bash
# Chạy start_pnj.sh trên VPS 31–40 (nohup để screen không chết khi SSH đóng).

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if ! command -v sshpass &>/dev/null; then
  echo "[!] Cần sshpass."
  exit 1
fi

declare -a IPS=(
  103.82.26.131 103.82.26.66 103.82.26.90 103.82.26.100 103.82.26.163
  103.82.26.189 103.82.26.144 103.82.26.47 103.82.26.240 103.82.26.52
)
declare -a PASS=(
  'Nw21W2QgPV9Mu456'   'U2NqJ85642zQS0MB'   '87Uzfnx7oqTvmc22'   'hajg1m0EJpB0cqz4'   'SeCK7J0056Z9NgJR'
  'q5ux9AmMMQMF0cJU'   'U59fZ47H98HZnM74'   '696eJMJZgFXK4fu5'   'C334zktt36SW7zJX'   '89Hs2t2JEvHm6KKp'
)

echo "=== Start PNJ (screen) trên VPS 31–40 ==="
for i in {31..40}; do
  idx=$((i - 31))
  ip="${IPS[$idx]}"
  pw="${PASS[$idx]}"
  sshpass -p "$pw" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@"$ip" \
    "cd /root/pnj_thantai 2>/dev/null && (nohup bash start_pnj.sh </dev/null >>/tmp/start_pnj.log 2>&1) & sleep 2; true" 2>/dev/null && echo "  VPS $i ($ip) đã gửi lệnh start." || echo "  VPS $i ($ip) bỏ qua."
done
echo "Xong. Kiểm tra: ./check_31_40_vps.sh"
