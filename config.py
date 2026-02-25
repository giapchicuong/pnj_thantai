"""
Cấu hình selectors cho automation PNJ Thần Tài.
"""

# URL trang chính
BASE_URL = "https://thantai.pnj.com.vn?utm_type=roadshow&utm_source=MTY&utm_medium=roadshow&utm_content=MTY_roadshow_HO"
BASE_ORIGIN = "https://thantai.pnj.com.vn"

# Các selector - dựa trên HTML thực tế
SELECTORS = {
    "chua_mua_hang": ["#btChuaMuaHang"],
    "phone_input": ["#txtSoDienThoai"],
    "captcha_input": ["#txtCaptcha"],
    "captcha_image": ["#dvCaptcha img[src*='/images/captcha/']", "img[src*='captcha']", "img[src*='Captcha']"],
    "captcha_refresh": ["img[onclick='LoadCaptcha()']", "img[src*='iconRefresh']"],
    "tich_loc_ngay": ["#xacnhansdt", "#dvBTXacNhanThongTin img"],
    "tich_loc_1_luot": ["#btTichLoc1Luot", "#dvChoiNgay img"],
    "tich_them_loc": ["img[onclick='closeKetQua()'][src*='btTichThemLoc']", "img[src*='btTichThemLoc']", "img[onclick='closeKetQua()']"],
    "ve_trang_chu": ["a[onclick='openHome()']", "img[src*='btVeTrangChu']", "#dvVeTrangChu input"],
    "popup_close": ["input[onclick='closeThongBao()']", "img[onclick='closeThongBao()']", ".form-close", "img[src*='close-circle']"],
    "so_luot_con_lai": ["#spSoLuotChoiConLai"],
}

# Loading: chờ ẩn (display:none) trước khi click
LOADING_SPIN = "#dvChoiNgay_Loading"
LOADING_TICH_LOC_NGAY = "#dvBTXacNhanThongTin_Loading"

# Cloudflare Turnstile (detect trang verify)
CLOUDFLARE_TURNSTILE = "iframe[src*='challenges.cloudflare.com']"

# Container popup kết quả: ConLuot = còn lượt, HetLuot = hết lượt
POPUP_CON_LOOT = "#dvButtonPopupKetQua_ConLuot"
POPUP_HET_LOOT = "#dvButtonPopupKetQua_HetLuot"

# Popup IP bị chặn (rotate proxy: quit driver + tạo mới = IP mới)
POPUP_IP_BLOCK = ["#dvContentThongBao", ".form-container-content"]
POPUP_IP_BLOCK_TEXT = "Có vấn đề xảy ra!"

CHECKBOX_TERMS = ["input[type='checkbox']", ".terms-checkbox"]

# Timeouts (giây)
TIMEOUT_ELEMENT = 10
TIMEOUT_PAGE_LOAD = 30
WAIT_AFTER_CLICK = 0.5
IMPLICIT_WAIT = 2
WAIT_AFTER_SPIN = 8
WAIT_FOR_POPUP_MAX = 25
WAIT_FOR_NEXT_SPIN = 30

NUM_WORKERS = 1  # Khuyến nghị ổn định trên VPS Linux (tránh crash Chrome đa luồng)
SUMMARY_INTERVAL = 120
MAX_RETRY_PER_PHONE = 3  # Retry tối đa mỗi SĐT khi lỗi (tránh loop vô hạn)
MAX_IP_ROTATE_PER_PHONE = 5  # Đổi IP tối đa mỗi SĐT khi bị chặn (quit + tạo driver mới)

# Chế độ tiết kiệm RAM. False = mở cửa sổ Chrome (ổn định hơn khi nhiều luồng)
LOW_MEMORY_MODE = True

# Dùng undetected-chromedriver để né Cloudflare (ẩn dấu automation)
USE_UNDETECTED = True

# Captcha - CHỈ DÙNG MIỄN PHÍ (ddddocr + Tesseract)
# Thứ tự: ddddocr -> Tesseract. Tỷ lệ đúng tùy captcha, số sai sẽ bỏ qua.
CAPTCHA_API_KEY = ""
CAPTCHA_USE_DDDDOCR = True
USE_MANUAL_FALLBACK = False
