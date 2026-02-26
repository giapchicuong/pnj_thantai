#!/bin/bash
# Script deploy PNJ Thần Tài lên VPS Ubuntu 20.04
# Chạy 1 worker, không proxy. Chạy: bash deploy_vps.sh

set -e
WORKERS=1
REPO_URL="https://github.com/giapchicuong/pnj_thantai.git"
INSTALL_DIR="$HOME/pnj_thantai"

echo "=== Deploy PNJ Thần Tài ==="
echo "  Workers: $WORKERS"
echo "  Thư mục: $INSTALL_DIR"
echo ""

# 0. Đợi dpkg/apt lock (tránh lỗi "Unable to acquire the dpkg frontend lock")
echo "[0/8] Đợi dpkg sẵn sàng..."
WAIT_MAX=24
i=0
while sudo fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1 || sudo fuser /var/lib/dpkg/lock >/dev/null 2>&1; do
  i=$((i + 1))
  if [ "$i" -ge "$WAIT_MAX" ]; then
    echo "  [!] Timeout đợi dpkg lock (2 phút). Thoát."
    exit 1
  fi
  echo "  Đợi lock apt/dpkg... (${i}/${WAIT_MAX})"
  sleep 5
done
echo "  Dpkg sẵn sàng."

# 1. Cập nhật hệ thống
echo "[1/8] Cập nhật hệ thống..."
sudo apt update -qq && sudo apt upgrade -y -qq

# 2. Cài gói hệ thống (tương thích Ubuntu 20/24)
echo "[2/8] Cài gói hệ thống..."
sudo apt install -y -qq \
  git wget curl unzip screen \
  tesseract-ocr tesseract-ocr-vie \
  libglib2.0-0 libnss3 libxss1 libgbm1
sudo apt install -y -qq libgl1-mesa-glx libasound2 2>/dev/null || \
  sudo apt install -y -qq libgl1 libasound2t64 2>/dev/null || true

# 3. Cài Google Chrome
echo "[3/8] Cài Google Chrome..."
if ! command -v google-chrome &>/dev/null; then
  wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
  echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
  sudo apt update -qq
  sudo apt install -y -qq google-chrome-stable
fi
echo "  Chrome: $(google-chrome --version 2>/dev/null || echo 'đã cài')"

# 4. Tăng /dev/shm (tránh Chrome crash)
echo "[4/8] Tăng /dev/shm lên 2GB..."
sudo mount -o remount,size=2G /dev/shm 2>/dev/null || true
df -h /dev/shm | tail -1

# 5. Cài Miniconda
echo "[5/8] Cài Miniconda..."
if [ ! -d "$HOME/miniconda3" ]; then
  wget -q https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh
  bash /tmp/miniconda.sh -b -p "$HOME/miniconda3"
  rm -f /tmp/miniconda.sh
  echo 'export PATH="$HOME/miniconda3/bin:$PATH"' >> "$HOME/.bashrc"
fi
export PATH="$HOME/miniconda3/bin:$PATH"

# 6. Chấp nhận Conda ToS và tạo env
echo "[6/8] Tạo môi trường Python 3.11..."
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main 2>/dev/null || true
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r 2>/dev/null || true
conda create -n pnj311 python=3.11 -y 2>/dev/null || true
if [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
  source "$HOME/miniconda3/etc/profile.d/conda.sh"
  conda activate pnj311
else
  source "$HOME/miniconda3/bin/activate" pnj311
fi

# 7. Clone repo và cài Python packages
echo "[7/8] Clone repo và cài packages..."
if [ ! -d "$INSTALL_DIR" ]; then
  git clone "$REPO_URL" "$INSTALL_DIR"
else
  cd "$INSTALL_DIR"
  git pull origin main 2>/dev/null || true
  cd - >/dev/null
fi

cd "$INSTALL_DIR"
pip install -q -r requirements.txt "ddddocr>=1.5,<1.6"
echo "  Packages đã cài."

# 8. Tạo phones.txt nếu chưa có
echo "[8/8] Kiểm tra phones.txt..."
if [ ! -s "$INSTALL_DIR/phones.txt" ]; then
  echo "# Thêm SĐT mỗi dòng 1 số" > "$INSTALL_DIR/phones.txt"
  echo "  [!] phones.txt trống - nhớ thêm SĐT vào file này!"
fi

# Tạo script chạy (1 worker)
cat > "$INSTALL_DIR/run_16gb.sh" << 'RUNSCRIPT'
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate pnj311
cd "$SCRIPT_DIR"
python main.py --workers 1 --headless --continuous --reload-interval 60 "$@"
RUNSCRIPT
chmod +x "$INSTALL_DIR/run_16gb.sh"

# Copy start_pnj.sh nếu có (chạy nền với screen)
if [ -f "$INSTALL_DIR/start_pnj.sh" ]; then
  chmod +x "$INSTALL_DIR/start_pnj.sh"
fi

echo ""
echo "=== Deploy xong ==="
echo ""
echo "Bước tiếp theo:"
echo "  1. Thêm SĐT vào $INSTALL_DIR/phones.txt (hoặc scp từ máy local)"
echo "  2. Chạy nền (KHÔNG cần giữ terminal):"
echo "       cd $INSTALL_DIR && bash start_pnj.sh"
echo "     Hoặc dùng systemd: bash install_service.sh rồi sudo systemctl start pnj-thantai"
echo "  3. Xem log: screen -r pnj (thoát: Ctrl+A D)"
echo ""
echo "Chi tiết 500k lượt: xem DEPLOY_500K.md"
echo "Cập nhật code: cd $INSTALL_DIR && git pull origin main"
echo ""
