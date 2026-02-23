#!/bin/bash
# Chạy trên VPS khi Chrome hay crash (Connection refused)
# Giải pháp: tăng /dev/shm + cài xvfb
# Chạy: ssh root@IP 'bash -s' < fix_chrome_shm.sh
# Hoặc: bash fix_chrome_shm.sh (trên VPS)

echo "[*] Tăng /dev/shm lên 2GB..."
sudo mount -o remount,size=2G /dev/shm 2>/dev/null && echo "  OK" || echo "  [!] Thất bại"
echo "[*] Cài xvfb (virtual display - tránh Chrome crash)..."
sudo apt-get update -qq && sudo apt-get install -y -qq xvfb 2>/dev/null && echo "  OK" || echo "  [!] Thất bại"
df -h /dev/shm 2>/dev/null
echo ""
echo "[*] Restart: cd ~/pnj_thantai && git pull && pkill -f main.py; screen -S pnj -X quit 2>/dev/null; sleep 2; bash start_pnj.sh"
