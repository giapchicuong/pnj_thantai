#!/bin/bash
# Setup 2 VPS: phones_57 -> 103.82.26.114, phones_58 -> 103.82.26.144
# Chạy: cd ~/path/to/pnj_thantai && bash setup_vps_57_58.sh

set -e
KEY="/Users/giapchicuong/Desktop/sshkey-97764149.pem"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 57: 103.82.26.114
echo "=== [57] 103.82.26.114 ==="
echo "  Deploy..."
ssh -i "$KEY" -o StrictHostKeyChecking=no root@103.82.26.114 "curl -sL https://raw.githubusercontent.com/giapchicuong/pnj_thantai/main/deploy_vps.sh | bash" || { echo "  [!] Deploy lỗi"; exit 1; }
echo "  Copy phones_57.txt..."
scp -i "$KEY" -o StrictHostKeyChecking=no "phones_57.txt" "root@103.82.26.114:~/pnj_thantai/phones.txt" || { echo "  [!] SCP lỗi"; exit 1; }
echo "  Pull + start..."
ssh -i "$KEY" root@103.82.26.114 "cd ~/pnj_thantai && cp not_completed.txt /tmp/nc.bak 2>/dev/null; git checkout -- not_completed.txt 2>/dev/null; rm -f run_16gb.sh; git pull origin main 2>/dev/null || true; cp /tmp/nc.bak not_completed.txt 2>/dev/null; bash start_pnj.sh"
echo "  [57] Xong."
echo ""

# 58: 103.82.26.144
echo "=== [58] 103.82.26.144 ==="
echo "  Deploy..."
ssh -i "$KEY" -o StrictHostKeyChecking=no root@103.82.26.144 "curl -sL https://raw.githubusercontent.com/giapchicuong/pnj_thantai/main/deploy_vps.sh | bash" || { echo "  [!] Deploy lỗi"; exit 1; }
echo "  Copy phones_58.txt..."
scp -i "$KEY" -o StrictHostKeyChecking=no "phones_58.txt" "root@103.82.26.144:~/pnj_thantai/phones.txt" || { echo "  [!] SCP lỗi"; exit 1; }
echo "  Pull + start..."
ssh -i "$KEY" root@103.82.26.144 "cd ~/pnj_thantai && cp not_completed.txt /tmp/nc.bak 2>/dev/null; git checkout -- not_completed.txt 2>/dev/null; rm -f run_16gb.sh; git pull origin main 2>/dev/null || true; cp /tmp/nc.bak not_completed.txt 2>/dev/null; bash start_pnj.sh"
echo "  [58] Xong."
echo ""
echo "=== Hoàn thành 2 instance ==="
