#!/bin/bash
# Kiểm tra VPS 59-70: cái nào chạy, cái nào không
# Tự động fix và start các VPS chưa chạy
# Chạy: bash check_and_fix_59_70.sh
#       bash check_and_fix_59_70.sh --all   (cập nhật + restart TẤT CẢ, áp dụng 5 workers)

FORCE_ALL=0
[ "$1" = "--all" ] || [ "$1" = "-a" ] && FORCE_ALL=1

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

get_ip() {
  case "$1" in
    59) echo "103.82.24.163";;
    60) echo "103.82.24.230";;
    61) echo "103.82.24.172";;
    62) echo "103.82.24.131";;
    63) echo "103.82.24.233";;
    64) echo "103.82.24.60";;
    65) echo "103.82.24.104";;
    66) echo "103.82.24.154";;
    67) echo "103.82.24.200";;
    68) echo "103.82.24.240";;
    69) echo "103.179.189.162";;
    70) echo "103.179.189.138";;
    *) echo "";;
  esac
}
get_pw() {
  case "$1" in
    59) echo "bwRMeTWFz20u2HGp";;
    60) echo "mWNQ2Y1b4czH3fK1";;
    61) echo "4s3E4U36m33KNj7X";;
    62) echo "Q8fUHm608VcrA92e";;
    63) echo "GdwTHEn7u264X14A";;
    64) echo "N2Nw3e90u10RT8gw";;
    65) echo "xNMNt35D154h57WR";;
    66) echo "GuB5Xhe759KtH8P4";;
    67) echo "3sS5UDHjMhywbxVB";;
    68) echo "10qxauX2uS548k9S";;
    69) echo "YWwx61uoNutSe9js";;
    70) echo "n5639ZN2beG5ChN6";;
    *) echo "";;
  esac
}

SSH_OPTS="-o StrictHostKeyChecking=no -o ConnectTimeout=15 -o ServerAliveInterval=30 -o ServerAliveCountMax=10"

check_one() {
  local ip="$1" pass="$2"
  # Kiểm tra process python main.py (chính xác hơn screen -ls)
  sshpass -p "$pass" ssh $SSH_OPTS root@$ip "pgrep -f 'main.py' >/dev/null && echo ok || echo no" 2>/dev/null || echo "fail"
}

fix_and_start_one() {
  local i="$1" ip="$2" pass="$3"
  echo "  [$i] Fix & start $ip..."
  # Nếu chưa có start_pnj.sh -> chạy deploy đầy đủ
  has_start=$(sshpass -p "$pass" ssh $SSH_OPTS root@$ip "test -f /root/pnj_thantai/start_pnj.sh && echo y" 2>/dev/null)
  if [ "$has_start" != "y" ]; then
    echo "  [$i] Deploy đầy đủ (chưa có code)..."
    sshpass -p "$pass" ssh $SSH_OPTS root@$ip "curl -sL https://raw.githubusercontent.com/giapchicuong/pnj_thantai/main/deploy_vps.sh | bash" 2>/dev/null || true
    sleep 5
  else
    sshpass -p "$pass" ssh $SSH_OPTS root@$ip "cd /root/pnj_thantai && git pull origin main 2>/dev/null || true" 2>/dev/null
  fi
  # SCP phones
  [ -f "phones_$i.txt" ] && sshpass -p "$pass" scp -o StrictHostKeyChecking=no "phones_$i.txt" "root@${ip}:/root/pnj_thantai/phones.txt" 2>/dev/null
  # Start
  sshpass -p "$pass" ssh $SSH_OPTS root@$ip "cd /root/pnj_thantai && bash start_pnj.sh" 2>/dev/null || true
  sleep 8
  # Kiểm tra lại
  result=$(check_one "$ip" "$pass")
  if [ "$result" = "ok" ]; then
    echo "  [$i] OK - đã chạy"
  else
    echo "  [$i] Chưa chạy (thử SSH thủ công: ssh root@$ip)"
  fi
}

# Update + restart 1 VPS (dừng cũ, git pull, start lại - áp dụng run_16gb 5 workers)
restart_one() {
  local i="$1" ip="$2" pass="$3"
  echo "  [$i] Update & restart $ip..."
  sshpass -p "$pass" ssh $SSH_OPTS root@$ip "pkill -f main.py 2>/dev/null; screen -S pnj -X quit 2>/dev/null; sleep 2; cd /root/pnj_thantai && git pull origin main 2>/dev/null || true" 2>/dev/null
  [ -f "phones_$i.txt" ] && sshpass -p "$pass" scp -o StrictHostKeyChecking=no "phones_$i.txt" "root@${ip}:/root/pnj_thantai/phones.txt" 2>/dev/null
  sshpass -p "$pass" ssh $SSH_OPTS root@$ip "cd /root/pnj_thantai && bash start_pnj.sh" 2>/dev/null || true
  sleep 8
  result=$(check_one "$ip" "$pass")
  [ "$result" = "ok" ] && echo "  [$i] OK - đã chạy 5 workers" || echo "  [$i] Chưa chạy"
}

echo "=== Kiểm tra VPS 59-70 ==="
echo ""

RUNNING=""
NOT_RUNNING=""

for i in $(seq 59 70); do
  ip=$(get_ip "$i")
  pass=$(get_pw "$i")
  [ -z "$ip" ] && continue
  result=$(check_one "$ip" "$pass")
  if [ "$result" = "ok" ]; then
    echo "[$i] $ip - Đang chạy"
    RUNNING="$RUNNING $i"
  elif [ "$result" = "fail" ]; then
    echo "[$i] $ip - Không kết nối được (VPS tắt?)"
    NOT_RUNNING="$NOT_RUNNING $i"
  else
    echo "[$i] $ip - Chưa chạy"
    NOT_RUNNING="$NOT_RUNNING $i"
  fi
done

echo ""
echo "Tóm tắt:"
echo "  Đang chạy:${RUNNING:- (không có)}"
echo "  Chưa chạy:${NOT_RUNNING:- (không có)}"

if [ "$FORCE_ALL" = "1" ]; then
  echo ""
  echo "=== [--all] Cập nhật + restart TẤT CẢ 59-70 (áp dụng 5 workers) ==="
  for i in $(seq 59 70); do
    ip=$(get_ip "$i")
    pass=$(get_pw "$i")
    [ -z "$ip" ] && continue
    result=$(check_one "$ip" "$pass")
    [ "$result" = "fail" ] && echo "  [$i] Bỏ qua (không SSH được)" && continue
    restart_one "$i" "$ip" "$pass"
  done
elif [ -n "$NOT_RUNNING" ]; then
  echo ""
  echo "=== Fix và start các VPS chưa chạy ==="
  for i in $NOT_RUNNING; do
    ip=$(get_ip "$i")
    pass=$(get_pw "$i")
    [ -z "$ip" ] && continue
    result=$(check_one "$ip" "$pass")
    [ "$result" = "fail" ] && echo "  [$i] Bỏ qua (không SSH được)" && continue
    fix_and_start_one "$i" "$ip" "$pass"
  done
  echo ""
  echo "=== Kiểm tra lại lần cuối ==="
  for i in $NOT_RUNNING; do
    ip=$(get_ip "$i")
    pass=$(get_pw "$i")
    [ -z "$ip" ] && continue
    result=$(check_one "$ip" "$pass")
    status="Chưa chạy"
    [ "$result" = "ok" ] && status="ĐÃ CHẠY"
    [ "$result" = "fail" ] && status="Lỗi kết nối"
    echo "  [$i] $ip - $status"
  done
fi

echo ""
echo "=== Xong ==="
