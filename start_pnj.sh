#!/bin/bash
# Chạy PNJ trong nền - không cần giữ terminal mở
# Dùng screen để có thể xem log sau: screen -r pnj
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SESSION="pnj"

# Nếu đã có session pnj đang chạy thì bỏ qua
if screen -ls | grep -q "\.$SESSION\s"; then
  echo "[!] Session 'pnj' đã chạy. Xem log: screen -r pnj"
  exit 1
fi

echo "[*] Khởi động PNJ trong screen (session: pnj)"
echo "[*] Xem log: screen -r pnj"
echo "[*] Thoát khỏi log (giữ chạy): Ctrl+A rồi D"
echo "[*] Dừng: screen -r pnj rồi Ctrl+C"
echo ""
cd "$SCRIPT_DIR"
# Dùng login shell để conda có trong PATH khi chạy trong screen
screen -dmS "$SESSION" bash -l -c "cd '$SCRIPT_DIR' && bash run_16gb.sh"
sleep 1
screen -ls | grep pnj
