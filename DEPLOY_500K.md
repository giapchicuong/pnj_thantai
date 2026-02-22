# Deploy 500.000 lượt chơi trong 4 ngày

## Tóm tắt

| Mục tiêu | Giá trị |
|----------|---------|
| Tổng lượt chơi | 500.000 |
| Thời gian | 4 ngày |
| Lượt/SĐT | 3 |
| **Tổng SĐT cần** | **~167.000** |

## Setup 35 instance (phones_1 .. phones_35)

| Instance | File | SĐT | Ghi chú |
|----------|------|-----|---------|
| 1–8 | phones_1..8.txt | ~25.000/instance | Đã có sẵn |
| 9–35 | phones_9..35.txt | ~7.400/instance | Tạo từ 200k: `python split_phones.py 27 phones_200k.txt 9` |

**Copy lên instance mới (9–35):**
1. Chỉnh IP trong `scp_phones_9_to_35.sh`
2. Chạy: `bash scp_phones_9_to_35.sh`
3. Trên mỗi instance: deploy (nếu chưa) → `cd ~/pnj_thantai && bash start_pnj.sh`

## Cấu hình instance

- **Mỗi instance:** 16GB RAM, 5 workers
- **Số instance:** 7–10 (tùy tốc độ thực tế)

## Bảng chi tiết

| Số instance | Workers tổng | SĐT/instance | Ghi chú |
|-------------|-------------|--------------|---------|
| 7 | 35 | ~23.860 | Tối thiểu, cần chạy ổn định |
| 8 | 40 | ~20.875 | Cân bằng |
| 10 | 50 | ~16.700 | An toàn, đạt nhanh hơn |

**Ước tính:** 5 workers × ~35 lượt/giờ × 20h/ngày × 4 ngày ≈ 14.000 lượt/instance

## Quy trình deploy

### 1. Chuẩn bị file phones.txt (trên máy local)

Có tổng ~167.000 SĐT trong 1 file `phones_all.txt` (mỗi dòng 1 số).

### 2. Chia cho từng instance

```bash
cd pnj_thantai
python split_phones.py 8 phones_all.txt
# Tạo phones_1.txt .. phones_8.txt
```

### 3. Deploy từng instance

SSH vào mỗi instance, chạy:

```bash
curl -sL https://raw.githubusercontent.com/giapchicuong/pnj_thantai/main/deploy_vps.sh | bash
```

### 4. Copy phones.txt vào mỗi instance

Trên máy local (chạy cho từng instance):

```bash
scp phones_1.txt root@<IP_INSTANCE_1>:~/pnj_thantai/phones.txt
scp phones_2.txt root@<IP_INSTANCE_2>:~/pnj_thantai/phones.txt
# ... tương tự
```

### 5. Chạy trên mỗi instance (không cần giữ terminal)

SSH vào từng instance, chạy **một lệnh** rồi thoát:

```bash
cd ~/pnj_thantai && bash start_pnj.sh
```

Sau đó **đóng terminal** – tool vẫn chạy trên VPS. Lặp lại cho tất cả instance.

## Chạy nền – không cần giữ terminal

### Cách 1: screen (đơn giản)

```bash
ssh root@<IP>
cd ~/pnj_thantai
screen -dmS pnj bash run_16gb.sh
```

- Chạy trong nền, thoát SSH vẫn chạy
- Xem log: `screen -r pnj` (thoát: Ctrl+A D)
- Dừng: `screen -r pnj` → Ctrl+C

### Cách 2: systemd (tự chạy khi boot)

Sau khi deploy, chạy:

```bash
bash ~/pnj_thantai/install_service.sh
```

Tool sẽ tự chạy khi VPS khởi động, chạy lại khi crash.

### Cách 3: nohup (đơn giản nhất)

```bash
cd ~/pnj_thantai
nohup bash run_16gb.sh > pnj.log 2>&1 &
```

- Log ghi vào `pnj.log`
- Dừng: `pkill -f "python main.py"`
