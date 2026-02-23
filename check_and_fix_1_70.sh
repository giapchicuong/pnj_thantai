#!/bin/bash
# Kiểm tra VPS 1-70: cái nào chạy, cái nào không
# Tự động fix và start các VPS chưa chạy
# Chạy: bash check_and_fix_1_70.sh
#       bash check_and_fix_1_70.sh --all   (cập nhật + restart TẤT CẢ, áp dụng 3 workers)
# Dữ liệu IP/Password: import từ Excel bằng python3 import_excel_and_run.py file.xlsx

FORCE_ALL=0
[ "$1" = "--all" ] || [ "$1" = "-a" ] && FORCE_ALL=1

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# get_ip và get_pw được cập nhật bởi import_excel_and_run.py
get_ip() {
  case "$1" in
    1) echo "103.82.22.18";;
    2) echo "103.82.22.50";;
    3) echo "103.82.22.28";;
    4) echo "103.82.22.241";;
    5) echo "103.82.23.216";;
    6) echo "103.179.173.92";;
    7) echo "103.179.173.54";;
    8) echo "103.179.173.53";;
    9) echo "103.82.27.79";;
    10) echo "103.82.27.23";;
    11) echo "103.82.27.6";;
    12) echo "103.82.27.196";;
    13) echo "103.82.27.230";;
    14) echo "103.82.27.151";;
    15) echo "103.82.27.24";;
    16) echo "103.82.27.62";;
    17) echo "103.82.27.126";;
    18) echo "103.82.27.217";;
    19) echo "222.255.180.183";;
    20) echo "222.255.180.68";;
    21) echo "103.166.184.237";;
    22) echo "103.166.184.252";;
    23) echo "103.166.184.39";;
    24) echo "103.166.184.97";;
    25) echo "103.166.184.172";;
    26) echo "103.166.184.61";;
    27) echo "103.166.184.253";;
    28) echo "222.255.180.53";;
    29) echo "103.82.23.227";;
    30) echo "103.166.184.174";;
    31) echo "103.166.184.200";;
    32) echo "103.166.184.68";;
    33) echo "103.179.189.64";;
    34) echo "103.179.189.39";;
    35) echo "103.82.26.44";;
    36) echo "103.82.24.101";;
    37) echo "103.82.25.59";;
    38) echo "103.82.24.106";;
    39) echo "103.82.24.38";;
    40) echo "103.82.24.70";;
    41) echo "103.82.24.111";;
    42) echo "103.82.24.46";;
    43) echo "103.82.24.33";;
    44) echo "103.166.185.245";;
    45) echo "103.82.195.167";;
    46) echo "103.82.195.127";;
    47) echo "103.82.26.130";;
    48) echo "103.179.189.19";;
    49) echo "103.179.189.240";;
    50) echo "103.179.189.140";;
    51) echo "103.179.189.127";;
    52) echo "103.179.189.164";;
    53) echo "103.179.189.57";;
    54) echo "103.179.189.245";;
    55) echo "103.179.189.121";;
    56) echo "103.179.189.105";;
    57) echo "103.82.26.114";;
    58) echo "103.82.26.144";;
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
    1) echo "06SaV5q3s8Vg70aB";;
    2) echo "EEfZ6G0y6CAQGbSW";;
    3) echo "36p7p0UuH6e5yAbc";;
    4) echo "X6A6D8kZAO9beY74";;
    5) echo "9zN29tpQDm6T9Ozw";;
    6) echo "pqpZwTtz2DVvWze0";;
    7) echo "YkcmSWbzqcAW8AGB";;
    8) echo "n97gS07erw6kK60y";;
    9) echo "3017OM7Ey1UY7Tf6";;
    10) echo "OCVwa8633880hdSS";;
    11) echo "xRK8UYn6Ba6UqMjY";;
    12) echo "sE2jHxJogTq0yDpd";;
    13) echo "r8FvQmj4bEFAn961";;
    14) echo "tT6gqJrkDFfBQ2pq";;
    15) echo "2xJ8vQzP8q5A6pz6";;
    16) echo "ZbJsTf6QeEf3RD45";;
    17) echo "0PwsxBP7Gaoms7gP";;
    18) echo "1U24AtmpNOap5pG4";;
    19) echo "FyNYegwof7a8fmsO";;
    20) echo "z7Ms9v41565ERPTw";;
    21) echo "zPrXJQ1N2t4W92Pw";;
    22) echo "3kkMRDvt72xK8snN";;
    23) echo "bgjGX82q3xo37Y88";;
    24) echo "We05f07k7bOvn276";;
    25) echo "jGr5A86au20b813p";;
    26) echo "coHGYAR2hhUOJ0P6";;
    27) echo "b2gq3SPrw7h3Jq1X";;
    28) echo "E8mKcj2umNpSq8o3";;
    29) echo "grNOsEQd7E921ru5";;
    30) echo "HHSRP88V4p19yspD";;
    31) echo "KJgUoAc3PFxrkRwB";;
    32) echo "5Z50D4nxZQ8SU69t";;
    33) echo "as173Z7DDBvpsURV";;
    34) echo "GSeGoe1R92Fdc21A";;
    35) echo "H7on0dxe8B7E4Qn5";;
    36) echo "SBX03JY5w98E9Yge";;
    37) echo "88puS0e4S1x73gCY";;
    38) echo "DGWhbY6m11A767jK";;
    39) echo "dsQzesOh6EBGdtZ2";;
    40) echo "3H9as9xrt5hKK9R5";;
    41) echo "bRrFykTj54QCCHb5";;
    42) echo "7jT1ZGHCx7fyp9n6";;
    43) echo "BhbP2MN1b8MhZZbh";;
    44) echo "AO1Vs3SW4DXryp4v";;
    45) echo "YcnmqkBvr73fxDB7";;
    46) echo "3d46e4eKYDVp1VR0";;
    47) echo "pJ2SMtBzxDM4856t";;
    48) echo "96wePPE9eDUjWrz8";;
    49) echo "7J0s7y961z3t8Y0X";;
    50) echo "gK9HNS1G9hOGOn8v";;
    51) echo "roA2QxCspkNuhb3X";;
    52) echo "53OPe9Z32R90NzZ9";;
    53) echo "yutdV3P9HguC8S1e";;
    54) echo "7HTw0YAbkusV1G34";;
    55) echo "B6j16RxrreHQm4Fx";;
    56) echo "sQsVG64evsx5K9dA";;
    57) echo "6j7361Ft5xPqpOCT";;
    58) echo "JkwAR02D1hp647bK";;
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
  # Phải có main.py VÀ process đang chạy - thiếu file = báo "chưa chạy" để fix
  sshpass -p "$pass" ssh $SSH_OPTS root@$ip "test -f /root/pnj_thantai/main.py && pgrep -f 'main.py' >/dev/null && echo ok || echo no" 2>/dev/null || echo "fail"
}

fix_and_start_one() {
  local i="$1" ip="$2" pass="$3"
  echo "  [$i] Fix & start $ip..."
  has_start=$(sshpass -p "$pass" ssh $SSH_OPTS root@$ip "test -f /root/pnj_thantai/start_pnj.sh && echo y" 2>/dev/null)
  if [ "$has_start" != "y" ]; then
    echo "  [$i] Deploy đầy đủ (chưa có code)..."
    sshpass -p "$pass" ssh $SSH_OPTS root@$ip "curl -sL https://raw.githubusercontent.com/giapchicuong/pnj_thantai/main/deploy_vps.sh | bash" 2>/dev/null || true
    sleep 5
  else
    sshpass -p "$pass" ssh $SSH_OPTS root@$ip "cd /root/pnj_thantai && git pull origin main 2>/dev/null || true" 2>/dev/null
  fi
  [ -f "phones_$i.txt" ] && sshpass -p "$pass" scp -o StrictHostKeyChecking=no "phones_$i.txt" "root@${ip}:/root/pnj_thantai/phones.txt" 2>/dev/null
  sshpass -p "$pass" ssh $SSH_OPTS root@$ip "cd /root/pnj_thantai && bash start_pnj.sh" 2>/dev/null || true
  sleep 8
  result=$(check_one "$ip" "$pass")
  [ "$result" = "ok" ] && echo "  [$i] OK - đã chạy" || echo "  [$i] Chưa chạy (thử SSH: ssh root@$ip)"
}

restart_one() {
  local i="$1" ip="$2" pass="$3"
  echo "  [$i] Update & restart $ip..."
  sshpass -p "$pass" ssh $SSH_OPTS root@$ip "pkill -f main.py 2>/dev/null; screen -S pnj -X quit 2>/dev/null; sleep 2; cd /root/pnj_thantai && git pull origin main 2>/dev/null || true" 2>/dev/null
  [ -f "phones_$i.txt" ] && sshpass -p "$pass" scp -o StrictHostKeyChecking=no "phones_$i.txt" "root@${ip}:/root/pnj_thantai/phones.txt" 2>/dev/null
  sshpass -p "$pass" ssh $SSH_OPTS root@$ip "cd /root/pnj_thantai && bash start_pnj.sh" 2>/dev/null || true
  sleep 8
  result=$(check_one "$ip" "$pass")
  [ "$result" = "ok" ] && echo "  [$i] OK - đã chạy 3 workers" || echo "  [$i] Chưa chạy"
}

echo "=== Kiểm tra VPS 1-70 ==="
echo ""

RUNNING=""
NOT_RUNNING=""

for i in $(seq 1 70); do
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
  echo "=== [--all] Cập nhật + restart TẤT CẢ 70→1 (đảo thứ tự: số sau chạy trước) ==="
  for i in $(seq 70 -1 1); do
    ip=$(get_ip "$i")
    pass=$(get_pw "$i")
    [ -z "$ip" ] && continue
    result=$(check_one "$ip" "$pass")
    [ "$result" = "fail" ] && echo "  [$i] Bỏ qua (không SSH được)" && continue
    restart_one "$i" "$ip" "$pass"
  done
elif [ -n "$NOT_RUNNING" ]; then
  echo ""
  echo "=== Fix và start các VPS chưa chạy (thứ tự 70→1) ==="
  for i in $(echo $NOT_RUNNING | tr ' ' '\n' | sort -nr); do
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
