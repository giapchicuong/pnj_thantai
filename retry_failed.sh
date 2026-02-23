#!/usr/bin/env bash
# Chỉ chạy lại các VPS trong setup_failed.txt
# (scp)/(start): bỏ deploy, chỉ SCP + start
# (deploy): chạy lại toàn bộ
# Cần bash 4+ (macOS: brew install bash) hoặc chạy: /opt/homebrew/bin/bash retry_failed.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FAILED_LOG="$SCRIPT_DIR/setup_failed.txt"
cd "$SCRIPT_DIR"

# Lookup IP và password (tương thích bash 3.2)
get_ip() {
  case "$1" in
    59) echo "103.82.24.163";;  60) echo "103.82.24.230";;  61) echo "103.82.24.172";;  62) echo "103.82.24.131";;
    63) echo "103.82.24.233";;  64) echo "103.82.24.60";;  65) echo "103.82.24.104";;  66) echo "103.82.24.154";;
    67) echo "103.82.24.200";;  68) echo "103.82.24.240";;  69) echo "103.179.189.162";;  70) echo "103.179.189.138";;
    *) echo "";;
  esac
}
get_pw() {
  case "$1" in
    59) echo "bwRMeTWFz20u2HGp";;  60) echo "mWNQ2Y1b4czH3fK1";;  61) echo "4s3E4U36m33KNj7X";;  62) echo "Q8fUHm608VcrA92e";;
    63) echo "GdwTHEn7u264X14A";;  64) echo "N2Nw3e90u10RT8gw";;  65) echo "xNMNt35D154h57WR";;  66) echo "GuB5Xhe759KtH8P4";;
    67) echo "3sS5UDHjMhywbxVB";;  68) echo "10qxauX2uS548k9S";;  69) echo "YWwx61uoNutSe9js";;  70) echo "n5639ZN2beG5ChN6";;
    *) echo "";;
  esac
}

SSH_OPTS="-o StrictHostKeyChecking=no -o ConnectTimeout=15 -o ServerAliveInterval=30 -o ServerAliveCountMax=10"
run_ssh() {
  sshpass -p "$2" ssh $SSH_OPTS root@$1 "$3"
}
run_scp() {
  sshpass -p "$2" scp -o StrictHostKeyChecking=no "$3" "root@${1}:/root/pnj_thantai/phones.txt"
}

do_scp() { run_scp "$1" "$2" "$3"; }
# start_pnj.sh exit 1 khi session đã chạy -> coi là thành công
do_pull_start() {
  run_ssh "$1" "$2" "mkdir -p /root/pnj_thantai; cd /root/pnj_thantai && cp not_completed.txt /tmp/nc.bak 2>/dev/null; git checkout -- not_completed.txt 2>/dev/null; rm -f run_16gb.sh; git pull origin main 2>/dev/null || true; cp /tmp/nc.bak not_completed.txt 2>/dev/null; bash start_pnj.sh || exit 0"
}

retry_deploy() {
  local max=5 ip="$1" pass="$2"
  for r in $(seq 1 $max); do
    if run_ssh "$ip" "$pass" "curl -sL https://raw.githubusercontent.com/giapchicuong/pnj_thantai/main/deploy_vps.sh | bash"; then return 0; fi
    [ $r -lt $max ] && echo "    Deploy retry $r/$max..." && sleep 10
  done
  return 1
}

[ ! -f "$FAILED_LOG" ] && echo "Không có setup_failed.txt" && exit 0

# Parse failed - đọc IP trực tiếp từ file
RETRY_ITEMS=""
while read -r line; do
  echo "$line" | grep -q '^#' && continue
  [ -z "$line" ] && continue
  i=$(echo "$line" | awk '{print $1}')
  ip_from_file=$(echo "$line" | awk '{print $2}')
  reason=$(echo "$line" | grep -oE '\([^)]+\)' | tr -d '()')
  [ -z "$i" ] || [ -z "$reason" ] && continue
  ip="${ip_from_file:-$(get_ip "$i" | tr -d ' ')}"
  [ -z "$ip" ] && continue
  RETRY_ITEMS="${RETRY_ITEMS}${RETRY_ITEMS:+ }$i|$ip|$reason"
done < "$FAILED_LOG"

[ -z "$RETRY_ITEMS" ] && echo "Không có instance cần retry" && exit 0

count=$(echo "$RETRY_ITEMS" | wc -w | tr -d ' ')
echo "Retry $count instance..."
cp "$FAILED_LOG" "$FAILED_LOG.bak" 2>/dev/null
echo "# Retry $(date)" > "$FAILED_LOG"

for item in $RETRY_ITEMS; do
  i="${item%%|*}"
  rest="${item#*|}"
  ip="${rest%%|*}"
  reason="${rest##*|}"
  pass=$(get_pw "$i")
  [ -z "$ip" ] || [ -z "$pass" ] && continue
  [ ! -f "phones_$i.txt" ] && echo "[$i] Thiếu phones_$i.txt" && continue

  if [ "$reason" = "scp" ] || [ "$reason" = "start" ]; then
    echo "[$i] === $ip (scp + start) ==="
    run_ssh "$ip" "$pass" "mkdir -p /root/pnj_thantai"
    if ! do_scp "$ip" "$pass" "phones_$i.txt"; then
      echo "[$i] SCP fail"; echo "$i $ip (scp)" >> "$FAILED_LOG"; echo ""; continue
    fi
    do_pull_start "$ip" "$pass" && echo "[$i] Xong." || echo "$i $ip (start)" >> "$FAILED_LOG"
  else
    echo "[$i] === $ip (full deploy) ==="
    retry_deploy "$ip" "$pass" || { echo "[$i] Deploy fail"; echo "$i $ip (deploy)" >> "$FAILED_LOG"; echo ""; continue; }
    do_scp "$ip" "$pass" "phones_$i.txt" || { echo "[$i] SCP fail"; echo "$i $ip (scp)" >> "$FAILED_LOG"; echo ""; continue; }
    do_pull_start "$ip" "$pass" && echo "[$i] Xong." || echo "$i $ip (start)" >> "$FAILED_LOG"
  fi
  echo ""
done

echo "=== Xong ==="
grep -v '^#' "$FAILED_LOG" | grep -v '^$' | sed 's/^/  /' 2>/dev/null && echo "Vẫn lỗi -> $FAILED_LOG"