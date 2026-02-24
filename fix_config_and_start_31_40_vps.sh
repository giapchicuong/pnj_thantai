#!/bin/bash
# Sửa config + start PNJ cho VPS 31–40. Mặc định cả 10; có thể chỉ định: ./fix_config_and_start_31_40_vps.sh 31 35 40

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if ! command -v sshpass &>/dev/null; then
  echo "[!] Cần sshpass."
  exit 1
fi

# VPS 31–40
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

if [ $# -gt 0 ]; then
  LIST=("$@")
else
  LIST=(31 32 33 34 35 36 37 38 39 40)
fi
echo "=== Sửa config + start PNJ (VPS 31–40: ${#LIST[@]} con) ==="
for i in "${LIST[@]}"; do
  idx=$((i - 31))
  ip="${IPS[$idx]}"
  pw="${PASS[$idx]}"
  if [ "$i" -le 33 ]; then url="$URL_MBC"; elif [ "$i" -le 36 ]; then url="$URL_DNB"; else url="$URL_HCM"; fi
  url_esc="${url//\'/\'\\\'\'}"
  sshpass -p "$pw" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=12 root@"$ip" \
    "cd /root/pnj_thantai && git checkout -- . 2>/dev/null; rm -rf __pycache__ 2>/dev/null; git pull && git checkout config.py && \
     printf '%s' '$url_esc' > .url_tmp && python3 -c \"
import re
url = open('.url_tmp').read().rstrip()
with open('config.py') as f: c = f.read()
c = re.sub(r'BASE_URL = \\\"[^\\\"]*\\\"', 'BASE_URL = \\\"' + url + '\\\"', c)
with open('config.py','w') as f: f.write(c)
\" && rm -f .url_tmp; (screen -S pnj -X quit 2>/dev/null || true); (pkill -f 'main.py' 2>/dev/null || true); sleep 2" 2>/dev/null
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
echo "Xong. Kiểm tra: ./check_31_40_vps.sh"
