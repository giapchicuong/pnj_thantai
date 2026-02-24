#!/bin/bash
# Setup 30 VPS mới: deploy, gán phones_1..30, 3 workers, chia đều 3 link (MBC/DNB/HCM).
# Chạy từ thư mục repo (có phones_1.txt .. phones_30.txt).
# Cần: sshpass (brew install sshpass hoặc apt install sshpass)

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if ! command -v sshpass &>/dev/null; then
  echo "[!] Cần cài sshpass: brew install sshpass (Mac) hoặc apt install sshpass (Linux)"
  exit 1
fi

# 30 IP và password (từ danh sách VPS)
declare -a IPS=(
  103.82.24.131 103.82.24.200 103.82.24.66 103.82.24.199 103.82.24.154
  103.82.24.38 103.82.24.106 103.82.24.163 103.82.24.240 103.82.24.70
  103.179.189.83 103.179.189.6 103.179.189.60 103.179.189.127 103.179.189.44
  103.179.189.160 103.179.189.89 103.179.189.32 103.166.184.50 103.179.189.162
  103.179.189.39 103.166.184.174 103.166.184.143 103.166.184.61 103.166.184.165
  103.166.184.221 103.166.184.252 103.166.184.39 103.166.184.237 103.166.184.247
)
declare -a PASS=(
  '8TZkkKpmduwEk3f8'   'Ort4mnsa2E8rRC75'   'SXc37uX54Ft10eyh'   '16eZ00936u2g4n9r'   'wR5Cypc9ucHCOTEC'
  'vE5SssXC4NpDSB6K'   '776wFjB2Cw784Kc'   'Mmb15YsfHuFwDU'   'MWyRX1yYerx8Twh'   'W96683qG7aQfs9kl'
  'OxXYTzB3u943xU32'   'YrpsJA32u1SYmcp4'   'Dsbz9G5nkw37tvfR'   '8jm5YGYYyVjr825d'   'r2t6fyRjHoZKw56A'
  'Mw5BnpGJwSAXPO'     '1nESUTA1vD8fSpuD'   '7K9DGRXyrrxDestk'   '5pWZHxpG9y93tdc'   '9YEVK9Wz9S1Z8djP'
  '9tEgv4qk4nOzn4r8'   '4B31612WDUnr2TE'   'UUXUoJ9wqfHS1Fv'   '4b222yCmBYTPc3pl'   'y7RQRwYKzk3555m'
  '78tBJ9GvNUc36r4R'   'WF3Wcjk7P0XGXYV'   '3Kc3w9Wq1K7p2gl'   'Om4054GxyF1HH80'   'sQ7a0fNM7om4b2M'
)

URL_MBC='https://thantai.pnj.com.vn?utm_type=roadshow&utm_source=MBC&utm_medium=roadshow&utm_content=MBC_roadshow_HO'
URL_DNB='https://thantai.pnj.com.vn?utm_type=roadshow&utm_source=DNB&utm_medium=roadshow&utm_content=DNB_roadshow_HO'
URL_HCM='https://thantai.pnj.com.vn?utm_type=roadshow&utm_source=HCM&utm_medium=roadshow&utm_content=HCM_roadshow_HO'

for i in {1..30}; do
  idx=$((i - 1))
  ip="${IPS[$idx]}"
  pw="${PASS[$idx]}"
  phones_file="phones_${i}.txt"
  if [ ! -f "$phones_file" ]; then
    echo "[!] VPS $i ($ip): Thiếu file $phones_file, bỏ qua."
    continue
  fi
  # Chia link: 1-10 MBC, 11-20 DNB, 21-30 HCM
  if [ "$i" -le 10 ]; then
    url="$URL_MBC"
    link_name="MBC"
  elif [ "$i" -le 20 ]; then
    url="$URL_DNB"
    link_name="DNB"
  else
    url="$URL_HCM"
    link_name="HCM"
  fi
  url_sed="${url//&/\\&}"
  echo ""
  echo "========== VPS $i / 30: $ip (phones_$i, $link_name, 3 workers) =========="
  # Xóa host key cũ (tránh lỗi REMOTE HOST IDENTIFICATION HAS CHANGED khi VPS mới cùng IP)
  ssh-keygen -R "$ip" 2>/dev/null || true
  # 1) Deploy (noninteractive để apt/debconf không hỏi)
  echo "[1/4] Deploy..."
  sshpass -p "$pw" ssh -o StrictHostKeyChecking=accept-new root@"$ip" "export DEBIAN_FRONTEND=noninteractive; curl -sL https://raw.githubusercontent.com/giapchicuong/pnj_thantai/main/deploy_vps.sh | bash" || { echo "[!] Deploy fail $ip"; continue; }
  # Đợi thư mục tồn tại (deploy tạo ~/pnj_thantai)
  for _ in 1 2 3 4 5 6 7 8 9 10; do
    sshpass -p "$pw" ssh -o StrictHostKeyChecking=no root@"$ip" "test -d ~/pnj_thantai" 2>/dev/null && break
    echo "    Đợi ~/pnj_thantai..."
    sleep 10
  done
  if ! sshpass -p "$pw" ssh -o StrictHostKeyChecking=no root@"$ip" "test -d ~/pnj_thantai" 2>/dev/null; then
    echo "[!] ~/pnj_thantai không tồn tại sau deploy, bỏ qua VPS $i."
    continue
  fi
  # 2) Copy phones
  echo "[2/4] Copy $phones_file -> phones.txt..."
  sshpass -p "$pw" scp -o StrictHostKeyChecking=no "$phones_file" root@"$ip":~/pnj_thantai/phones.txt
  # 3) Git pull, set BASE_URL, set 3 workers, start
  echo "[3/4] Git pull + config URL + 3 workers..."
  sshpass -p "$pw" ssh -o StrictHostKeyChecking=no root@"$ip" "cd ~/pnj_thantai && git pull && sed -i 's|BASE_URL = \".*\"|BASE_URL = \"'"$url_sed"'\"|' config.py && sed -i 's/--workers [0-9]*/--workers 3/' run_16gb.sh"
  echo "[4/4] Start PNJ (screen)..."
  sshpass -p "$pw" ssh -o StrictHostKeyChecking=no root@"$ip" "cd ~/pnj_thantai && bash start_pnj.sh"
  echo "[OK] VPS $i ($ip) đã chạy."
done
echo ""
echo "=== Xong 30 VPS. Mỗi con: 3 luồng, 10 con/link (MBC/DNB/HCM). ==="
