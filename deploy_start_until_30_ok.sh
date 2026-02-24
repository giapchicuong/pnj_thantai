#!/bin/bash
# Deploy + start 30 VPS, kiểm tra và retry đến khi đủ 30/30 đang chạy.
# Chạy từ thư mục repo. Lặp tới khi check báo 30/30 OK (không giới hạn vòng).

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if ! command -v sshpass &>/dev/null; then
  echo "[!] Cần cài sshpass: brew install sshpass (Mac) hoặc apt install sshpass (Linux)"
  exit 1
fi

echo "=== Deploy + Start — chạy tới khi đủ 30/30 (sẽ retry mãi đến khi xong) ==="
echo ""

# Vòng 1: deploy + start toàn bộ 30
echo "--- Vòng 1: Setup toàn bộ 30 VPS ---"
./setup_30_vps.sh
echo ""

round=1
last_failed_list=""
same_fail_count=0
while true; do
  echo "--- Đợi 45s rồi kiểm tra ---"
  sleep 45

  out=$(./check_30_vps.sh 2>&1)
  echo "$out"
  echo ""

  ok_count=$(echo "$out" | grep "Kết quả:" | sed -n 's/.* \([0-9]*\)\/30.*/\1/p' || echo "0")
  if [ -z "$ok_count" ]; then ok_count=0; fi

  if [ "$ok_count" -eq 30 ]; then
    echo "=== Đủ 30/30 VPS đang chạy. Hoàn tất. ==="
    exit 0
  fi

  failed_list=$(echo "$out" | grep 'VPS [0-9]*.*FAIL' | sed -n 's/^VPS \([0-9]*\).*/\1/p' | tr '\n' ' ' | sed 's/ $//')
  if [ -z "$failed_list" ]; then
    echo "[!] Không parse được danh sách FAIL, coi như toàn bộ lỗi."
    failed_list="1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30"
  fi

  # Nếu cùng danh sách lỗi 3 vòng liên tiếp → có thể sai mật khẩu, thoát để tránh lặp vô hạn
  if [ "$failed_list" = "$last_failed_list" ]; then
    same_fail_count=$((same_fail_count + 1))
    if [ "$same_fail_count" -ge 3 ]; then
      echo ""
      echo "=== Cùng $((same_fail_count)) vòng liên tiếp các VPS sau vẫn lỗi: $failed_list ==="
      echo "Thường do SSH Permission denied (sai mật khẩu hoặc VPS đổi pass)."
      echo "Kiểm tra mảng PASS trong setup_30_vps.sh và check_30_vps.sh; xem setup_logs/setup_vps_*.log."
      echo "Sửa xong chạy lại: ./deploy_start_until_30_ok.sh"
      exit 1
    fi
  else
    same_fail_count=0
  fi
  last_failed_list="$failed_list"

  round=$((round + 1))
  echo "--- Vòng $round: Retry setup các VPS lỗi: $failed_list ---"
  ./setup_30_vps.sh $failed_list
  echo ""
  echo "Đợi 60s trước khi check lại..."
  sleep 60
done
