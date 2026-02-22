# PNJ Thần Tài - Tool Tích Lộc

Tool automation sử dụng Python + Selenium + Tesseract + OpenCV để tích lộc hàng loạt cho danh sách số điện thoại trên trang PNJ Thần Tài.

## Luồng xử lý

1. **Chưa mua hàng** → Bấm nút vào luồng chưa mua hàng
2. **Nhập SĐT + Captcha** → Điền số điện thoại, giải captcha bằng OCR
3. **Tích Lộc Ngay** → Bấm nút bắt đầu
4. **Quay 3 lượt** → Bấm "Tích Lộc 1 Lượt" / "Tích thêm lộc" (3 lượt/số)
5. **Về trang chủ** → Bấm nút về trang chủ
6. Lặp lại từ bước 1 cho số tiếp theo

## Cài đặt

### 1. Tesseract OCR

**macOS:**
```bash
brew install tesseract tesseract-lang
```

**Ubuntu:**
```bash
sudo apt install tesseract-ocr tesseract-ocr-vie
```

**Windows:** Tải từ [GitHub](https://github.com/UB-Mannheim/tesseract/wiki) và cài. Sau đó thêm biến môi trường `TESSERACT_CMD` (hoặc chỉnh trong `captcha_solver.py`).

### 2. Python & dependencies

```bash
cd pnj_thantai
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Chrome

Cần cài Google Chrome. `webdriver-manager` sẽ tự tải ChromeDriver tương thích.

## Sử dụng

1. Thêm danh sách số điện thoại vào `phones.txt` (mỗi dòng 1 số):

```
0901234567
0912345678
0987654321
...
```

2. **Cập nhật selectors** trong `config.py` theo DOM thực tế của trang. Bạn cung cấp `id`, `class`, `name` hoặc CSS/XPath cho từng nút.

3. Chạy:

```bash
python main.py
```

### Chạy nhiều luồng (nhanh hơn)

```bash
python main.py --workers 18
```

### Mục tiêu 500.000 lượt / 7–10 ngày (laptop 16GB)

- Cần ~166.667 SĐT (mỗi SĐT 3 lượt)
- Dùng 15–20 workers (config mặc định: 18)
- Chạy liên tục, reload `phones.txt` khi hết:

```bash
python main.py --workers 18 --headless --continuous --reload-interval 60
# hoặc
./run_500k.sh
```

- Dừng: `Ctrl+C`
- Cập nhật `phones.txt` với batch SĐT mới khi đang chạy; script sẽ load lại sau mỗi batch

## Cấu hình selectors (config.py)

Các key trong `SELECTORS` tương ứng:

| Key | Mô tả |
|-----|-------|
| `chua_mua_hang` | Nút "Chưa mua hàng" |
| `phone_input` | Ô nhập số điện thoại |
| `captcha_input` | Ô nhập captcha |
| `captcha_image` | Thẻ img chứa ảnh captcha |
| `captcha_refresh` | Nút refresh captcha (optional) |
| `tich_loc_ngay` | Nút "Tích Lộc Ngay" |
| `tich_loc_1_luot` | Nút "Tích Lộc 1 Lượt" |
| `tich_them_loc` | Nút "Tích thêm lộc" |
| `ve_trang_chu` | Nút "Về trang chủ" |

Mỗi key có thể là danh sách selectors; tool sẽ thử lần lượt cho đến khi tìm thấy.

**Ví dụ cấu hình khi bạn đã có id/class:**

```python
"chua_mua_hang": ["#btn-chua-mua-hang"],
"phone_input": ["input#phone", "input[name='phone']"],
"tich_loc_ngay": ["button.tich-loc-ngay"],
```

## Chạy headless

Trong `main.py`, bỏ comment dòng:
```python
options.add_argument("--headless=new")
```

## Xử lý Captcha (miễn phí)

- **ddddocr** (mặc định): `CAPTCHA_USE_DDDDOCR = True`
- **Tesseract**: `CAPTCHA_USE_DDDDOCR = False`

**Để dùng ddddocr (nhận captcha tốt hơn):** Dùng Python 3.11, xem [SETUP_PY311.md](SETUP_PY311.md).

## Deploy lên VPS (Ubuntu 20.04, 16GB RAM)

Chạy trên **mỗi instance mới** (một lệnh):

```bash
curl -sL https://raw.githubusercontent.com/giapchicuong/pnj_thantai/main/deploy_vps.sh | bash
```

Hoặc clone rồi chạy:

```bash
git clone https://github.com/giapchicuong/pnj_thantai.git
cd pnj_thantai
bash deploy_vps.sh
```

Script sẽ: cài Chrome, Miniconda, Python 3.11, packages, tăng /dev/shm. Sau đó:

```bash
# Thêm SĐT vào phones.txt (hoặc dùng split_phones.py để chia cho nhiều instance)
cd ~/pnj_thantai
bash run_16gb.sh   # 5 workers (16GB RAM)
# Chạy nền: screen -S pnj && bash run_16gb.sh
```

**Chia SĐT cho nhiều instance:** (xem [DEPLOY_500K.md](DEPLOY_500K.md) để đạt 500k lượt)
```bash
python split_phones.py 8 phones_all.txt   # Tạo phones_1.txt .. phones_8.txt
# scp phones_X.txt root@IP:~/pnj_thantai/phones.txt
```

**Chạy nền (không cần giữ terminal):**
```bash
bash start_pnj.sh    # Chạy trong screen, thoát SSH vẫn chạy
# Xem log: screen -r pnj
```

## Lưu ý

- Khi chạy nhiều luồng, cần `USE_UNDETECTED = True` trong `config.py` (tránh lỗi ChromeDriver exit -9 trên macOS).
- Có thể chỉnh thời gian chờ (`WAIT_AFTER_CLICK`, `WAIT_AFTER_SPIN`) trong `config.py` nếu trang load chậm.
