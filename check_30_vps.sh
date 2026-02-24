#!/bin/bash
# Kiểm tra 30 VPS PNJ: main.py đang chạy + phones.txt có dữ liệu = OK (screen không bắt buộc).
# Chạy: ./check_30_vps.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if ! command -v sshpass &>/dev/null; then
  echo "[!] Cần cài sshpass: brew install sshpass (Mac) hoặc apt install sshpass (Linux)"
  exit 1
fi

# IP + pass theo Excel sadsad.xlsx STT 1-30
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

OK_COUNT=0
FAIL_COUNT=0
declare -a FAIL_LIST

echo "=== Kiểm tra 30 VPS PNJ ==="
echo ""

for i in {1..30}; do
  idx=$((i - 1))
  ip="${IPS[$idx]}"
  pw="${PASS[$idx]}"
  if [ "$i" -le 10 ]; then link="MBC"; elif [ "$i" -le 20 ]; then link="DNB"; else link="HCM"; fi

  out=$(sshpass -p "$pw" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@"$ip" \
    "screen -ls 2>/dev/null | grep -q pnj && echo SCREEN_OK; \
     pgrep -f 'main.py' >/dev/null && echo PYTHON_OK; \
     test -s /root/pnj_thantai/phones.txt && echo PHONES_OK" 2>/dev/null) || out=""

  screen_ok=; python_ok=; phones_ok=
  echo "$out" | grep -q SCREEN_OK && screen_ok=1
  echo "$out" | grep -q PYTHON_OK && python_ok=1
  echo "$out" | grep -q PHONES_OK && phones_ok=1

  # OK = main.py + phones + screen (có screen thì mới vào được screen -r pnj xem log)
  if [[ -n "$python_ok" && -n "$phones_ok" && -n "$screen_ok" ]]; then
    echo "VPS $i ($ip) [$link]  OK  (main.py + phones + screen)"
    ((OK_COUNT++)) || true
  else
    if [[ -n "$python_ok" && -n "$phones_ok" ]]; then
      echo "VPS $i ($ip) [$link]  FAIL  (chạy nhưng không có screen — chạy lại: ./fix_config_and_start_30_vps.sh)"
    else
      echo "VPS $i ($ip) [$link]  FAIL  (screen=$screen_ok python=$python_ok phones=$phones_ok)"
    fi
    ((FAIL_COUNT++)) || true
    FAIL_LIST+=("$i:$ip")
  fi
done

echo ""
echo "=== Kết quả: $OK_COUNT/30 đang chạy ổn ==="
if [ "$FAIL_COUNT" -gt 0 ]; then
  echo "Lỗi: $FAIL_COUNT con — ${FAIL_LIST[*]}"
fi
