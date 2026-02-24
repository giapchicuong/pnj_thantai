#!/bin/bash
# Restart 70 VPS với số mới (phones_1.txt .. phones_70.txt, mỗi file 10.000 số)
# Chạy: bash restart_with_new_phones.sh
#       bash restart_with_new_phones.sh /path/to/excel.xlsx

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

XLSX="${1:-/Users/giapchicuong/Desktop/3829864_260223155302.xlsx}"

# Kiểm tra đã có 70 file phones chưa
missing=0
for i in $(seq 1 70); do
  [ -f "phones_$i.txt" ] || missing=$((missing+1))
done
if [ "$missing" -gt 0 ]; then
  echo "[!] Thiếu $missing file phones_X.txt. Chạy trước: python3 create_phones_70x10k.py"
  exit 1
fi

echo "[*] Có đủ 70 file phones. Import Excel và restart 70 VPS..."
python3 import_excel_and_run.py "$XLSX"
