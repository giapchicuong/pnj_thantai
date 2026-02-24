#!/bin/bash
# Setup 10 VPS 31–40: deploy, gán phones_31..phones_40, 2 workers, chia link MBC/DNB/HCM.
# Chạy từ thư mục repo. Cần: sshpass
# Chạy: ./setup_31_40_vps.sh   hoặc chỉ một số: ./setup_31_40_vps.sh 31 35 40

PARALLEL=10
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
LOG_DIR="$SCRIPT_DIR/setup_logs"
mkdir -p "$LOG_DIR"

if ! command -v sshpass &>/dev/null; then
  echo "[!] Cần cài sshpass: brew install sshpass (Mac) hoặc apt install sshpass (Linux)"
  exit 1
fi

# VPS 31–40: IP + pass (bạn cung cấp)
declare -a IPS=(
  103.82.26.131 103.82.26.66 103.82.26.90 103.82.26.100 103.82.26.163
  103.82.26.189 103.82.26.144 103.82.26.47 103.82.26.240 103.82.26.52
)
declare -a PASS=(
  'Nw21W2QgPV9Mu456'   'U2NqJ85642zQS0MB'   '87Uzfnx7oqTvmc22'   'hajg1m0EJpB0cqz4'   'SeCK7J0056Z9NgJR'
  'q5ux9AmMMQMF0cJU'   'U59fZ47H98HZnM74'   '696eJMJZgFXK4fu5'   'C334zktt36SW7zJX'   '89Hs2t2JEvHm6KKp'
)
URL_MBC='https://thantai.pnj.com.vn?utm_type=roadshow&utm_source=MBC&utm_medium=roadshow&utm_content=MBC_roadshow_HO'
URL_DNB='https://thantai.pnj.com.vn?utm_type=roadshow&utm_source=DNB&utm_medium=roadshow&utm_content=DNB_roadshow_HO'
URL_HCM='https://thantai.pnj.com.vn?utm_type=roadshow&utm_source=HCM&utm_medium=roadshow&utm_content=HCM_roadshow_HO'

setup_one() {
  local i=$1 ip=$2 pw=$3 url_sed=$4 phones_file=$5 link_name=$6 url=$7
  if [ ! -f "$phones_file" ]; then
    echo "[VPS $i] Thiếu $phones_file, bỏ qua."
    return 1
  fi
  echo "[VPS $i] Bắt đầu $ip [$link_name]..."
  ssh-keygen -R "$ip" 2>/dev/null || true

  if ! sshpass -p "$pw" ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=30 -o ServerAliveInterval=20 -o ServerAliveCountMax=30 root@"$ip" "export DEBIAN_FRONTEND=noninteractive; curl -sL https://raw.githubusercontent.com/giapchicuong/pnj_thantai/main/deploy_vps.sh | bash"; then
    echo "[VPS $i] Deploy fail $ip (xem setup_vps_$i.log)"
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
  url_esc="${url//\'/\'\\\'\'}"
  sshpass -p "$pw" ssh -o StrictHostKeyChecking=no root@"$ip" "cd /root/pnj_thantai && git pull && printf '%s' '$url_esc' > .url_tmp && python3 -c \"
import re
url = open('.url_tmp').read()
with open('config.py') as f: c = f.read()
c = re.sub(r'BASE_URL = \\\"[^\\\"]*\\\"', 'BASE_URL = \\\"' + url.rstrip() + '\\\"', c)
with open('config.py','w') as f: f.write(c)
\" && rm -f .url_tmp && sed -i 's/--workers [0-9]*/--workers 2/' run_16gb.sh" 2>/dev/null
  sshpass -p "$pw" ssh -o StrictHostKeyChecking=no root@"$ip" "cd /root/pnj_thantai && nohup bash -c 'bash start_pnj.sh' </dev/null >>/tmp/start_pnj.log 2>&1 &" 2>/dev/null
  sleep 2
  echo "[VPS $i] OK $ip"
}

if [ $# -gt 0 ]; then
  INDICES=("$@")
else
  INDICES=(31 32 33 34 35 36 37 38 39 40)
fi
echo "=== Setup VPS 31–40 (${#INDICES[@]} con, song song $PARALLEL) ==="
echo "Log: $LOG_DIR/setup_vps_*.log"
echo ""

running=0
for i in "${INDICES[@]}"; do
  while [ $running -ge $PARALLEL ]; do
    wait -n 2>/dev/null || wait
    running=$((running - 1))
  done
  idx=$((i - 31))
  ip="${IPS[$idx]}"
  pw="${PASS[$idx]}"
  phones_file="$SCRIPT_DIR/phones_${i}.txt"
  if [ "$i" -le 33 ]; then url="$URL_MBC"; link_name="MBC"
  elif [ "$i" -le 36 ]; then url="$URL_DNB"; link_name="DNB"
  else url="$URL_HCM"; link_name="HCM"; fi
  url_sed="${url//&/\\&}"
  echo "[$(date +%H:%M:%S)] VPS $i ($ip) — log: setup_vps_$i.log"
  ( setup_one "$i" "$ip" "$pw" "$url_sed" "$phones_file" "$link_name" "$url" >> "$LOG_DIR/setup_vps_$i.log" 2>&1; echo $? > "$LOG_DIR/setup_vps_${i}.exit" ) &
  running=$((running + 1))
done
echo "[$(date +%H:%M:%S)] Đã gửi đủ ${#INDICES[@]} job, đang chờ..."
wait
echo ""
echo "=== Xong. Kiểm tra: ./check_31_40_vps.sh ==="
failed=0
for i in "${INDICES[@]}"; do
  if [ -f "$LOG_DIR/setup_vps_${i}.exit" ] && [ "$(cat "$LOG_DIR/setup_vps_${i}.exit")" != "0" ]; then
    echo "  VPS $i lỗi: xem $LOG_DIR/setup_vps_$i.log"
    failed=$((failed + 1))
  fi
done
[ $failed -eq 0 ] && echo "Tất cả ${#INDICES[@]} con đã chạy." || echo "Lỗi $failed con — xem log trên."
