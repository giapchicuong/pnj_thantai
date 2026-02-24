#!/bin/bash
# Sửa config.py (BASE_URL) + start PNJ. Mặc định cả 30 VPS; có thể chỉ định: ./fix_config_and_start_30_vps.sh 4 30

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if ! command -v sshpass &>/dev/null; then
  echo "[!] Cần sshpass."
  exit 1
fi

# IP + pass lấy từ sadsad.xlsx (cột IPv4, Password) — cập nhật: python3 update_vps_credentials_from_excel.py
declare -a IPS=(
  103.82.24.131 103.82.24.200 103.82.24.66 103.82.24.199 103.82.24.154
  103.82.24.38 103.82.24.106 103.82.24.163 103.82.24.240 103.82.24.70
  103.179.189.83 103.179.189.6 103.179.189.60 103.179.189.127 103.179.189.44
  103.179.189.160 103.179.189.89 103.179.189.32 103.166.184.50 103.179.189.162
  103.179.189.39 103.166.184.174 103.166.184.143 103.166.184.61 103.166.184.165
  103.166.184.221 103.166.184.252 103.166.184.39 103.166.184.237 103.166.184.247
)
declare -a PASS=(
  '8TZkkKpmduwEk3f8'   'Ort4mnsa2E8rRC75'   'SXc37uX54Ft10eyh'   '16eZ0o936u2g4n9r'   'wR5Cypc9ucHCoTEd'
  'vE5SssXC4NpDSB6K'   '776wFjB2Cw784Kc2'   'Mmb15YsfHuFwDUkN'   'MWyRX1yYerx8TwhM'   'W96683qG7aQfs9kE'
  'OxXYTzB3u943xU32'   'YrpsJA32u1SYmcp4'   'Dsbz9G5nkw37tvfR'   '8jm5YGYYyVjr825d'   'r2t6fyRjHoZKw56A'
  'Mw5BnpGJwSAXP06T'   '1nESUTA1vD8fSpuD'   '7K9DGRXyrrxDestk'   '5pWZHxpG9y93tdc5'   '9YEVK9Wz9S1Z8djP'
  '9tEgv4qk4nOzn4r8'   '4B31612WDUnr2TEA'   'UUXUoJ9wqfHS1Fv6'   '4b222yCmBYTPc3pk'   'y7RQRwYKzk3555m4'
  '78tBJ9GvNUc36r4R'   'WF3Wcjk7P0XGXYV9'   '3Kc3w9Wq1K7p2gMg'   'Om4O54GxyF1HH8O9'   'sQ7a0fNM7om4b2Mq'
)
URL_MBC='https://thantai.pnj.com.vn?utm_type=roadshow&utm_source=MBC&utm_medium=roadshow&utm_content=MBC_roadshow_HO'
URL_DNB='https://thantai.pnj.com.vn?utm_type=roadshow&utm_source=DNB&utm_medium=roadshow&utm_content=DNB_roadshow_HO'
URL_HCM='https://thantai.pnj.com.vn?utm_type=roadshow&utm_source=HCM&utm_medium=roadshow&utm_content=HCM_roadshow_HO'

if [ $# -gt 0 ]; then
  LIST=("$@")
else
  LIST=(1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30)
fi
echo "=== Sửa config + start PNJ (${#LIST[@]} VPS) ==="
for i in "${LIST[@]}"; do
  idx=$((i-1))
  ip="${IPS[$idx]}"
  pw="${PASS[$idx]}"
  if [ "$i" -le 10 ]; then url="$URL_MBC"; elif [ "$i" -le 20 ]; then url="$URL_DNB"; else url="$URL_HCM"; fi
  url_esc="${url//\'/\'\\\'\'}"
  # Lần 1: lấy code mới nhất (reset --hard, tránh lỗi merge) + sửa config + kill
  sshpass -p "$pw" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=12 root@"$ip" \
    "cd /root/pnj_thantai && git fetch origin 2>/dev/null; git reset --hard origin/main 2>/dev/null; rm -rf __pycache__ 2>/dev/null; \
     printf '%s' '$url_esc' > .url_tmp && python3 -c \"
import re
url = open('.url_tmp').read().rstrip()
with open('config.py') as f: c = f.read()
c = re.sub(r'BASE_URL = \\\"[^\\\"]*\\\"', 'BASE_URL = \\\"' + url + '\\\"', c)
with open('config.py','w') as f: f.write(c)
\" && rm -f .url_tmp; (screen -S pnj -X quit 2>/dev/null || true); (pkill -f 'main.py' 2>/dev/null || true); sleep 2" 2>/dev/null
  # Lần 2: chỉ start — lệnh đơn giản, dùng exit code này để báo OK/FAIL
  out=$(sshpass -p "$pw" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=12 root@"$ip" \
    'cd /root/pnj_thantai && (nohup bash start_pnj.sh </dev/null >>/tmp/start_pnj.log 2>&1) & sleep 3; true' 2>&1)
  rc=$?
  if [ "$rc" -eq 0 ]; then
    echo "  VPS $i ($ip) OK"
  else
    echo "  VPS $i ($ip) FAIL"
    echo "$out" | head -5
  fi
done
echo ""
echo "Xong. Kiểm tra: ./check_30_vps.sh"
echo "Nếu VPS 4 hoặc 30 vẫn FAIL: có thể chưa có thư mục /root/pnj_thantai — chạy: ./setup_30_vps.sh 4 30"
