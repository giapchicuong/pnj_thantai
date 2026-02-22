#!/bin/bash
# Cài systemd service - PNJ tự chạy khi boot, tự restart khi crash
# Chạy: bash install_service.sh
# Sau khi cài: sudo systemctl start pnj-thantai
# Xem log: journalctl -u pnj-thantai -f
# Dừng: sudo systemctl stop pnj-thantai

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Chạy như user nào sở hữu thư mục pnj_thantai
OWNER=$(stat -c '%U' "$SCRIPT_DIR" 2>/dev/null || echo "root")
HOME_DIR=$(eval echo ~$OWNER)

sudo tee /etc/systemd/system/pnj-thantai.service > /dev/null << EOF
[Unit]
Description=PNJ Thần Tài - Tích Lộc
After=network.target

[Service]
Type=simple
User=$OWNER
WorkingDirectory=$SCRIPT_DIR
ExecStart=$HOME_DIR/miniconda3/envs/pnj311/bin/python $SCRIPT_DIR/main.py --workers 2 --headless --continuous --reload-interval 60
Restart=on-failure
RestartSec=30
Environment=PATH=$HOME_DIR/miniconda3/bin:/usr/local/bin:/usr/bin:/bin

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
echo ""
echo "[*] Đã cài service pnj-thantai"
echo ""
echo "Lệnh:"
echo "  Khởi động: sudo systemctl start pnj-thantai"
echo "  Dừng:      sudo systemctl stop pnj-thantai"
echo "  Trạng thái: sudo systemctl status pnj-thantai"
echo "  Tự chạy khi boot: sudo systemctl enable pnj-thantai"
echo "  Xem log:   journalctl -u pnj-thantai -f"
echo ""
