#!/bin/bash
# Copy phones_9.txt .. phones_35.txt lên 27 instance mới
# Chỉnh IP_9 .. IP_35 cho đúng các instance của bạn, rồi chạy: bash scp_phones_9_to_35.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# === CHỈNH CÁC IP SAU CHO ĐÚNG ===
IP_9=""
IP_10=""
IP_11=""
IP_12=""
IP_13=""
IP_14=""
IP_15=""
IP_16=""
IP_17=""
IP_18=""
IP_19=""
IP_20=""
IP_21=""
IP_22=""
IP_23=""
IP_24=""
IP_25=""
IP_26=""
IP_27=""
IP_28=""
IP_29=""
IP_30=""
IP_31=""
IP_32=""
IP_33=""
IP_34=""
IP_35=""

for i in $(seq 9 35); do
  ip_var="IP_$i"
  ip="${!ip_var}"
  if [ -n "$ip" ]; then
    echo "[$i/35] scp phones_$i.txt -> root@$ip:~/pnj_thantai/phones.txt"
    scp -o StrictHostKeyChecking=no "phones_$i.txt" "root@$ip:~/pnj_thantai/phones.txt" && echo "  OK" || echo "  FAIL"
  else
    echo "[$i/35] Bỏ qua (chưa set IP_$i)"
  fi
done

echo ""
echo "Xong. Trên mỗi instance mới, chạy: ssh root@IP 'cd ~/pnj_thantai && bash start_pnj.sh'"
