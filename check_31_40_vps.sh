#!/bin/bash
# Kiểm tra VPS 31–40: main.py + phones.txt + screen pnj.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if ! command -v sshpass &>/dev/null; then
  echo "[!] Cần sshpass: brew install sshpass (Mac) hoặc apt install sshpass (Linux)"
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

OK_COUNT=0
FAIL_COUNT=0
declare -a FAIL_LIST

echo "=== Kiểm tra VPS 31–40 ==="
echo ""

for i in {31..40}; do
  idx=$((i - 31))
  ip="${IPS[$idx]}"
  pw="${PASS[$idx]}"
  if [ "$i" -le 33 ]; then link="MBC"; elif [ "$i" -le 36 ]; then link="DNB"; else link="HCM"; fi

  out=$(sshpass -p "$pw" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@"$ip" \
    "screen -ls 2>/dev/null | grep -q pnj && echo SCREEN_OK; \
     pgrep -f 'main.py' >/dev/null && echo PYTHON_OK; \
     test -s /root/pnj_thantai/phones.txt && echo PHONES_OK" 2>/dev/null) || out=""

  screen_ok=; python_ok=; phones_ok=
  echo "$out" | grep -q SCREEN_OK && screen_ok=1
  echo "$out" | grep -q PYTHON_OK && python_ok=1
  echo "$out" | grep -q PHONES_OK && phones_ok=1

  if [[ -n "$python_ok" && -n "$phones_ok" && -n "$screen_ok" ]]; then
    echo "VPS $i ($ip) [$link]  OK  (main.py + phones + screen)"
    ((OK_COUNT++)) || true
  else
    if [[ -n "$python_ok" && -n "$phones_ok" ]]; then
      echo "VPS $i ($ip) [$link]  FAIL  (chạy nhưng không có screen — chạy lại: ./fix_config_and_start_31_40_vps.sh)"
    else
      echo "VPS $i ($ip) [$link]  FAIL  (screen=$screen_ok python=$python_ok phones=$phones_ok)"
    fi
    ((FAIL_COUNT++)) || true
    FAIL_LIST+=("$i:$ip")
  fi
done

echo ""
echo "=== Kết quả: $OK_COUNT/10 đang chạy ổn ==="
if [ "$FAIL_COUNT" -gt 0 ]; then
  echo "Lỗi: $FAIL_COUNT con — ${FAIL_LIST[*]}"
fi
