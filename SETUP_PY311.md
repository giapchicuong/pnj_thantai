# Cài Python 3.11 + ddddocr 1.5 (miễn phí, không mất tiền)

Chạy lần lượt trong Terminal:

## Bước 0: Chấp nhận Terms of Service (Conda)

Nếu gặp lỗi `CondaToSNonInteractiveError`:

```bash
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r
```

## Bước 1: Tạo môi trường Python 3.11

```bash
cd /Users/giapchicuong/kinfri/pnj_thantai
conda create -n pnj311 python=3.11 -y
```

## Bước 2: Kích hoạt và cài package

```bash
conda activate pnj311
pip install -r requirements.txt
pip install "ddddocr>=1.5,<1.6"
```

## Bước 3: Chạy tool

```bash
conda activate pnj311
python main.py
```

---

**Lưu ý:** Mỗi lần mở terminal mới cần gõ `conda activate pnj311` trước khi chạy `python main.py`.

**Xóa khi không dùng:** `conda env remove -n pnj311`
