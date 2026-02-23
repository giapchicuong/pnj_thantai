#!/bin/bash
# Setup VPS 59-70 với sshpass (tự động nhập mật khẩu)
# Chạy: bash setup_vps_59_70.sh
# Cần: brew install sshpass (hoặc brew install hudochenkov/sshpass/sshpass)

KEY="/Users/giapchicuong/Desktop/sshkey-97764149.pem"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FAILED_LOG="$SCRIPT_DIR/setup_failed.txt"
cd "$SCRIPT_DIR"

# IP và password cho 59-70
declare -A IPS=(
  [59]="103.82.24.163"
  [60]="103.82.24.230"
  [61]="103.82.24.172"
  [62]="103.82.24.131"
  [63]="103.82.24.233"
  [64]="103.82.24.60"
  [65]="103.82.24.104"
  [66]="103.82.24.154"
  [67]="103.82.24.200"
  [68]="103.82.24.240"
  [69]="103.179.189.162"
  [70]="103.179.189.138"
)
declare -A PW=(
  [59]="bwRMeTWFz20u2HGp"
  [60]="mWNQ2Y1b4czH3fK1"
  [61]="4s3E4U36m33KNj7X"
  [62]="Q8fUHm608VcrA92e"
  [63]="GdwTHEn7u264X14A"
  [64]="N2Nw3e90u10RT8gw"
  [65]="xNMNt35D154h57WR"
  [66]="GuB5Xhe759KtH8P4"
  [67]="3sS5UDHjMhywbxVB"
  [68]="10qxauX2uS548k9S"
  [69]="YWwx61uoNutSe9js"
  [70]="n5639ZN2beG5ChN6"
)

SSH_OPTS="-o StrictHostKeyChecking=no -o ConnectTimeout=15 -o ServerAliveInterval=30 -o ServerAliveCountMax=10"
run_ssh() {
  local ip="$1" pass="$2" cmd="$3"
  if [ -n "$pass" ]; then
    sshpass -p "$pass" ssh $SSH_OPTS root@$ip "$cmd"
  else
    ssh -i "$KEY" $SSH_OPTS root@$ip "$cmd"
  fi
}

run_scp() {
  local ip="$1" pass="$2" src="$3" dest="$4"
  if [ -n "$pass" ]; then
    sshpass -p "$pass" scp -o StrictHostKeyChecking=no "$src" "root@${ip}:${dest}"
  else
    scp -i "$KEY" -o StrictHostKeyChecking=no "$src" "root@${ip}:${dest}"
  fi
}

retry_cmd() {
  local max=3 ip="$1" pass="$2" fn="$3" sleep_sec=3
  shift 3
  for r in $(seq 1 $max); do
    if "$fn" "$ip" "$pass" "$@"; then
      return 0
    fi
    if [ $r -lt $max ]; then
      echo "    Lần $r thất bại, thử lại ($((r+1))/$max) trong ${sleep_sec}s..."
      sleep $sleep_sec
    fi
  done
  return 1
}

# Retry riêng cho deploy (curl|bash): 5 lần, sleep 10s - đa phần lỗi ở bước này
retry_deploy() {
  local max=5 ip="$1" pass="$2" sleep_sec=10
  for r in $(seq 1 $max); do
    if run_ssh "$ip" "$pass" "curl -sL https://raw.githubusercontent.com/giapchicuong/pnj_thantai/main/deploy_vps.sh | bash"; then
      return 0
    fi
    if [ $r -lt $max ]; then
      echo "    Deploy lần $r thất bại, thử lại ($((r+1))/$max) trong ${sleep_sec}s..."
      sleep $sleep_sec
    fi
  done
  return 1
}

do_scp() {
  run_scp "$1" "$2" "$3" "/root/pnj_thantai/phones.txt"
}

do_pull_start() {
  run_ssh "$1" "$2" "mkdir -p ~/pnj_thantai; cd ~/pnj_thantai && cp not_completed.txt /tmp/nc.bak 2>/dev/null; git checkout -- not_completed.txt 2>/dev/null; rm -f run_16gb.sh; git pull origin main 2>/dev/null || true; cp /tmp/nc.bak not_completed.txt 2>/dev/null; bash start_pnj.sh"
}

# Setup 1 VPS (chạy trong background)
setup_one() {
  local i="$1"
  local ip="${IPS[$i]}" pass="${PW[$i]}"
  local tag="[$i]"
  [ -z "$ip" ] && return 0
  if [ ! -f "$SCRIPT_DIR/phones_$i.txt" ]; then
    echo "$tag Thiếu phones_$i.txt" && echo "$i $ip (thiếu file)" >> "$FAILED_LOG"
    return 0
  fi

  echo "$tag === $ip (bắt đầu) ==="
  if ! retry_deploy "$ip" "$pass"; then
    echo "$tag Deploy thất bại sau 5 lần."
    echo "$i $ip (deploy)" >> "$FAILED_LOG"
    return 1
  fi

  echo "$tag Copy phones_$i.txt..."
  run_ssh "$ip" "$pass" "mkdir -p /root/pnj_thantai" 2>/dev/null || true
  if ! retry_cmd "$ip" "$pass" do_scp "phones_$i.txt"; then
    echo "$tag SCP thất bại sau 3 lần."
    echo "$i $ip (scp)" >> "$FAILED_LOG"
    return 1
  fi

  echo "$tag Pull + start..."
  if ! retry_cmd "$ip" "$pass" do_pull_start; then
    echo "$tag Pull/start thất bại."
    echo "$i $ip (start)" >> "$FAILED_LOG"
  else
    echo "$tag Xong."
  fi
}

# Số VPS chạy cùng lúc (12 = tất cả; 6 = chia đôi)
PARALLEL=12

# Xóa log cũ
echo "# VPS bị bỏ qua - chạy lại thủ công: $(date)" > "$FAILED_LOG"

if ! command -v sshpass &>/dev/null; then
  echo "[!] Cần cài sshpass: brew install sshpass"
  echo "    Hoặc: brew install hudochenkov/sshpass/sshpass"
  exit 1
fi

echo "Chạy $PARALLEL VPS đồng thời..."
for i in $(seq 59 70); do
  [ -z "${IPS[$i]}" ] && continue
  setup_one $i &
done
wait

echo ""
echo "=== Hoàn thành ==="
if [ -s "$FAILED_LOG" ] && [ $(wc -l < "$FAILED_LOG" | tr -d ' ') -gt 1 ]; then
  echo "Các instance bị bỏ qua: $FAILED_LOG"
fi
