#!/bin/bash
# Setup nhiều VPS một lần - chỉnh IP bên dưới rồi chạy: bash setup_vps_batch.sh

KEY="/Users/giapchicuong/Desktop/sshkey-97764149.pem"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# === CHỈNH IP TƯƠNG ỨNG VỚI phones_X.txt ===
declare -A IPS=(
  [58]="103.82.26.144"
  [59]=""
  [60]=""
  [61]=""
  [62]=""
  [63]=""
  [64]=""
  [65]=""
  [66]=""
  [67]=""
  [68]=""
  [69]=""
  [70]=""
  [71]=""
  [72]=""
  [73]=""
  [74]=""
  [75]=""
  [76]=""
)

for i in $(seq 57 76); do
  ip="${IPS[$i]}"
  [ -z "$ip" ] && continue
  [ ! -f "phones_$i.txt" ] && echo "[$i] Thiếu phones_$i.txt, bỏ qua." && continue

  echo "=== [$i] $ip ==="
  echo "  Deploy..."
  if ! ssh -i "$KEY" -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@$ip "curl -sL https://raw.githubusercontent.com/giapchicuong/pnj_thantai/main/deploy_vps.sh | bash"; then
    echo "  [!] Deploy lỗi, bỏ qua."
    echo ""
    continue
  fi
  echo "  Copy phones_$i.txt..."
  if ! scp -i "$KEY" -o StrictHostKeyChecking=no "phones_$i.txt" "root@$ip:~/pnj_thantai/phones.txt"; then
    echo "  [!] SCP lỗi, bỏ qua."
    echo ""
    continue
  fi
  echo "  Pull + start..."
  ssh -i "$KEY" root@$ip "cd ~/pnj_thantai && cp not_completed.txt /tmp/nc.bak 2>/dev/null; git checkout -- not_completed.txt 2>/dev/null; rm -f run_16gb.sh; git pull origin main 2>/dev/null || true; cp /tmp/nc.bak not_completed.txt 2>/dev/null; bash start_pnj.sh" || true
  echo "  [$i] Xong."
  echo ""
done

echo "=== Hoàn thành ==="
