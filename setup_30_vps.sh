#!/bin/bash
# Setup 30 VPS mới (SONG SONG): deploy, gán phones_1..30, 3 workers, chia đều 3 link.
# Chạy từ thư mục repo. Cần: sshpass
# Chạy song song: 15 VPS/lô (nhanh). Có thể tăng PARALLEL=30 để chạy cả 30 cùng lúc.

PARALLEL=30
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
LOG_DIR="$SCRIPT_DIR/setup_logs"
mkdir -p "$LOG_DIR"

if ! command -v sshpass &>/dev/null; then
  echo "[!] Cần cài sshpass: brew install sshpass (Mac) hoặc apt install sshpass (Linux)"
  exit 1
fi

# IP đúng theo Excel sadsad.xlsx STT 1-30 (VPS 1-10 MBC, 11-20 DNB, 21-30 HCM)
declare -a IPS=(
  103.82.24.131 103.82.24.200 103.82.24.66 103.82.24.199 103.82.24.154
  103.82.24.38 103.82.24.106 103.82.24.163 103.82.24.240 103.82.24.70
  103.179.189.83 103.179.189.6 103.179.189.60 103.179.189.127 103.179.189.44
  103.179.189.160 103.179.189.89 103.179.189.32 103.166.184.50 103.179.189.162 103.179.189.39
  103.166.184.174 103.166.184.143 103.166.184.61 103.166.184.165
  103.166.184.221 103.166.184.252 103.166.184.39 103.166.184.237 103.166.184.247
)
declare -a PASS=(
  '8TZkkKpmduwEk3f8'   'Ort4mnsa2E8rRC75'   'SXc37uX54Ft10eyh'   '16eZ0o936u2g4n9r'   'wR5Cypc9ucHCoTEd'
  'vE5SssXC4NpDSB6K'   '776wFjB2Cw784Kc2'   'Mmb15YsfHuFwDUkN'   'MWyRX1yYerx8TwhM'   'W96683qG7aQfs9kE'
  'OxXYTzB3u943xU32'   'YrpsJA32u1SYmcp4'   'Dsbz9G5nkw37tvfR'   '8jm5YGYYyVjr825d'   'r2t6fyRjHoZKw56A'
  'Mw5BnpGJwSAXP06T'   '1nESUTA1vD8fSpuD'   '7K9DGRXyrrxDestk'   '5pWZHxpG9y93tdc5'   '9YEVK9Wz9S1Z8djP'   '9tEgv4qk4nOzn4r8'
  '4B31612WDUnr2TEA'   'UUXUoJ9wqfHS1Fv6'   '4b222yCmBYTPc3pk'   'y7RQRwYKzk3555m4'
  '78tBJ9GvNUc36r4R'   'WF3Wcjk7P0XGXYV9'   '3Kc3w9Wq1K7p2gMg'   'Om4O54GxyF1HH8O9'   'sQ7a0fNM7om4b2Mq'
)

URL_MBC='https://thantai.pnj.com.vn?utm_type=roadshow&utm_source=MBC&utm_medium=roadshow&utm_content=MBC_roadshow_HO'
URL_DNB='https://thantai.pnj.com.vn?utm_type=roadshow&utm_source=DNB&utm_medium=roadshow&utm_content=DNB_roadshow_HO'
URL_HCM='https://thantai.pnj.com.vn?utm_type=roadshow&utm_source=HCM&utm_medium=roadshow&utm_content=HCM_roadshow_HO'

setup_one() {
  local i=$1 ip=$2 pw=$3 url_sed=$4 phones_file=$5 link_name=$6
  if [ ! -f "$phones_file" ]; then
    echo "[VPS $i] Thiếu $phones_file, bỏ qua."
    return 1
  fi
  echo "[VPS $i] Bắt đầu $ip [$link_name]..."
  ssh-keygen -R "$ip" 2>/dev/null || true

  if ! sshpass -p "$pw" ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=30 -o ServerAliveInterval=20 -o ServerAliveCountMax=30 root@"$ip" "export DEBIAN_FRONTEND=noninteractive; curl -sL https://raw.githubusercontent.com/giapchicuong/pnj_thantai/main/deploy_vps.sh | bash"; then
    echo "[VPS $i] Deploy fail $ip (xem lỗi trên hoặc setup_vps_$i.log)"
    return 1
  fi

  sleep 5
  local wait_count=0
  while [ $wait_count -lt 30 ]; do
    sshpass -p "$pw" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@"$ip" "test -d /root/pnj_thantai" 2>/dev/null && break
    sleep 10
    wait_count=$((wait_count + 1))
  done
  if ! sshpass -p "$pw" ssh -o StrictHostKeyChecking=no root@"$ip" "test -d /root/pnj_thantai" 2>/dev/null; then
    echo "[VPS $i] /root/pnj_thantai không tồn tại, bỏ qua."
    return 1
  fi

  sshpass -p "$pw" scp -o StrictHostKeyChecking=no "$phones_file" root@"$ip":/root/pnj_thantai/phones.txt 2>/dev/null || { echo "[VPS $i] scp fail"; return 1; }
  # Ghi BASE_URL bằng Python (tránh sed làm hỏng config do & trong URL)
  url_esc="${url//\'/\'\\\'\'}"
  sshpass -p "$pw" ssh -o StrictHostKeyChecking=no root@"$ip" "cd /root/pnj_thantai && git pull && printf '%s' '$url_esc' > .url_tmp && python3 -c \"
import re
url = open('.url_tmp').read()
with open('config.py') as f: c = f.read()
c = re.sub(r'BASE_URL = \\\"[^\\\"]*\\\"', 'BASE_URL = \\\"' + url.rstrip() + '\\\"', c)
with open('config.py','w') as f: f.write(c)
\" && rm -f .url_tmp && sed -i 's/--workers [0-9]*/--workers 2/' run_16gb.sh" 2>/dev/null
  # Chạy start_pnj.sh bằng nohup + nền để screen không bị tắt khi SSH đóng
  sshpass -p "$pw" ssh -o StrictHostKeyChecking=no root@"$ip" "cd /root/pnj_thantai && nohup bash -c 'bash start_pnj.sh' </dev/null >>/tmp/start_pnj.log 2>&1 &" 2>/dev/null
  sleep 2
  echo "[VPS $i] OK $ip"
}

# Cho phép chỉ chạy một số VPS: ./setup_30_vps.sh 4 5 6
if [ $# -gt 0 ]; then
  INDICES=("$@")
else
  INDICES=(1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30)
fi
echo "=== Setup ${#INDICES[@]} VPS (song song $PARALLEL con/lô) ==="
echo "Log từng con: $LOG_DIR/setup_vps_*.log"
echo ""

running=0
for i in "${INDICES[@]}"; do
  while [ $running -ge $PARALLEL ]; do
    wait -n 2>/dev/null || wait
    running=$((running - 1))
  done
  idx=$((i - 1))
  ip="${IPS[$idx]}"
  pw="${PASS[$idx]}"
  phones_file="$SCRIPT_DIR/phones_${i}.txt"
  if [ "$i" -le 10 ]; then url="$URL_MBC"; link_name="MBC"
  elif [ "$i" -le 20 ]; then url="$URL_DNB"; link_name="DNB"
  else url="$URL_HCM"; link_name="HCM"; fi
  url_sed="${url//&/\\&}"
  echo "[$(date +%H:%M:%S)] Khởi động VPS $i/30 ($ip) — log: setup_vps_$i.log"
  ( setup_one "$i" "$ip" "$pw" "$url_sed" "$phones_file" "$link_name" >> "$LOG_DIR/setup_vps_$i.log" 2>&1; echo $? > "$LOG_DIR/setup_vps_${i}.exit" ) &
  running=$((running + 1))
done
echo "[$(date +%H:%M:%S)] Đã gửi đủ ${#INDICES[@]} job, đang chờ..."
wait
echo ""
echo "=== Xong. Kiểm tra: ./check_30_vps.sh ==="
failed=0
for i in "${INDICES[@]}"; do
  if [ -f "$LOG_DIR/setup_vps_${i}.exit" ] && [ "$(cat "$LOG_DIR/setup_vps_${i}.exit")" != "0" ]; then
    echo "  VPS $i lỗi: xem $LOG_DIR/setup_vps_$i.log"
    failed=$((failed + 1))
  fi
done
[ $failed -eq 0 ] && echo "Tất cả ${#INDICES[@]} con đã chạy (xem log nếu cần)." || echo "Lỗi $failed con — xem log trên."
