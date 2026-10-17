# VNPAY Sandbox Python Integration - Seminar Demo
Dự án mẫu minh họa quy trình tích hợp cổng thanh toán trực tuyến **VNPAY Sandbox (FastAPI - Python)** phục vụ báo cáo seminar môn học. 

Tài liệu này cung cấp hướng dẫn cài đặt từng bước để người nghe có thể tự đăng ký tài khoản thử nghiệm, cấu hình và thực hành giao dịch ngay tại lớp, đồng thời làm rõ kiến trúc bảo mật với thuật toán băm **HMAC-SHA512**.

---

## 🚀 HƯỚNG DẪN THỰC HÀNH TẠI LỚP (QUICK START)

### Bước 1: Tải mã nguồn về máy tính
Mở **Terminal** (macOS/Linux) hoặc **PowerShell / Command Prompt / Git Bash** (Windows) và chạy lệnh:
```bash
git clone https://github.com/FogzxJE/vnpay-sandbox-python.git
cd vnpay-sandbox-python
```
*(Nếu máy không cài sẵn Git: Truy cập link GitHub của dự án -> Nhấn nút xanh **Code** -> Chọn **Download ZIP** -> Giải nén ra thư mục và mở cửa sổ dòng lệnh tại thư mục đó).*

---

### Bước 2: Cài đặt các gói phụ thuộc
Cài đặt trực tiếp 3 thư viện cần thiết (không bắt buộc dùng virtualenv):
```bash
pip install -r requirements.txt
```
*(Hoặc cài trực tiếp bằng lệnh: `pip install fastapi uvicorn pydantic`)*

---

### Bước 3: Đăng ký tài khoản VNPAY Sandbox cá nhân (1 phút)
1. Mở trình duyệt web truy cập trang đăng ký chính thức của VNPAY:
   👉 **https://sandbox.vnpayment.vn/devreg/**
2. Điền thông tin vào biểu mẫu:
   - **Tên website:** `VNStore` (hoặc tên tùy chọn)
   - **Địa chỉ URL:** `https://myvnpaydemo.vn` *(lưu ý: VNPAY yêu cầu định dạng tên miền hợp lệ như .vn, .com)*
   - **Email đăng ký:** Điền email thật đang sử dụng
   - **Mật khẩu:** Nhập mật khẩu tùy chọn
3. Nhập mã Captcha và bấm **Đăng ký**.
4. Mở hộp thư Email (kiểm tra cả mục **Spam / Thư rác**) để nhận:
   - **Mã Website (Terminal ID / vnp_TmnCode)**
   - **Chuỗi bí mật kết nối (Hash Secret / vnp_HashSecret)**

---

### Bước 4: Cấu hình thông tin vào dự án
Mở file **`config.py`** trong thư mục dự án và dán thông tin bạn vừa nhận từ email vào:

```python
VNPAY_TMN_CODE = "DÁN_TERMINAL_ID_CỦA_BẠN_VÀO_ĐÂY"
VNPAY_HASH_SECRET = "DÁN_HASH_SECRET_CỦA_BẠN_VÀO_ĐÂY"
```
*(Nhấn `Ctrl + S` để lưu file).*

---

### Bước 5: Khởi chạy ứng dụng
Chạy lệnh khởi động máy chủ API tại Terminal:
```bash
uvicorn main:app --reload --port 8000
```
- Mở trình duyệt web và truy cập: **http://127.0.0.1:8000**
- Giao diện đơn hàng **VNStore** xuất hiện, nhấn nút **"Tiến hành thanh toán"** để chuyển hướng sang Cổng thanh toán VNPAY Sandbox.

---

## 💳 THÔNG TIN THẺ TEST ĐỂ THANH TOÁN THÀNH CÔNG

Khi giao diện Cổng VNPAY hiển thị, chọn phương thức **Thẻ nội địa & tài khoản ngân hàng** -> chọn ngân hàng **NCB** và điền thông tin thẻ test của VNPAY:

| Trường thông tin | Dữ liệu nhập thử nghiệm |
| :--- | :--- |
| **Ngân hàng** | NCB |
| **Số thẻ** | `9704198526191432198` |
| **Tên chủ thẻ** | `NGUYEN VAN A` |
| **Ngày phát hành** | `07/15` |
| **Mã OTP** | Nhập `123456` và bấm **Xác nhận** |

- **Kết quả nhận được:** Hệ thống tự động chuyển hướng về trang biên nhận hiển thị thông báo **✓ Thanh Toán Thành Công** kèm mã kiểm tra chữ ký số **Hợp lệ (HMAC-SHA512 OK)**.

---

## 🧪 CÁC KỊCH BẢN KIỂM THỬ TRƯỚC LỚP (DEMO CASES)

1. **Kịch bản 1: Thanh toán thành công (Happy Path)**
   - Thực hiện thanh toán theo thông tin thẻ NCB mẫu ở trên.
   - Kết quả: Giao diện xanh lá cây, mã kết quả `vnp_ResponseCode = 00`, chữ ký số nguyên vẹn.

2. **Kịch bản 2: Khách hàng hủy giao dịch (Cancelled Transaction)**
   - Bấm tạo đơn hàng từ trang chủ, khi chuyển sang cổng VNPAY thì bấm **"Hủy thanh toán / Quay lại"**.
   - Kết quả: Trả về trang thông báo vàng cam với mã lỗi `vnp_ResponseCode = 24`, chữ ký vẫn hợp lệ vì do chính VNPAY trả về.

3. **Kịch bản 3: Tấn công giả mạo dữ liệu đường truyền (Data Tampering Attack)**
   - Tại URL của trang kết quả thành công, thử sửa tham số số tiền từ `vnp_Amount=5000000` thành `vnp_Amount=1000` rồi nhấn Enter.
   - Kết quả: Hàm băm phát hiện chuỗi dữ liệu không khớp với chữ ký `vnp_SecureHash`, giao diện lập tức chuyển cảnh báo màu đỏ: **"Cảnh Báo: Chữ ký không hợp lệ!"**.

---

## 📚 TỔNG QUAN LÝ THUYẾT (WHAT - WHY - HOW - WHEN)

### 1. WHAT (Đề tài trình bày nội dung gì?)
- **VNPAY Payment Gateway:** Giải pháp cổng thanh toán trực tuyến trung gian, kết nối giữa website thương mại điện tử với hệ sinh thái ngân hàng và ví điện tử.
- **VNPAY Sandbox:** Môi trường giả lập cung cấp API, giao diện thanh toán và thẻ ngân hàng ảo, cho phép nhà phát triển tích hợp và kiểm thử toàn diện quy trình thanh toán mà không làm phát sinh chi phí tiền tệ thực tế.

### 2. WHY (Vì sao cần tích hợp Sandbox & dùng chữ ký số?)
- **Kiểm thử quy trình khép kín:** Đảm bảo toàn bộ luồng tạo đơn, chuyển hướng và ghi nhận giao dịch hoạt động chuẩn xác trước khi triển khai môi trường thực tế (Production).
- **Đảm bảo tính toàn vẹn (Integrity):** Chống lại các cuộc tấn công man-in-the-middle hoặc người dùng tự ý chỉnh sửa giá trị đơn hàng trên URL trình duyệt.
- **Xác thực nguồn gốc (Authenticity):** Nhờ cơ chế chữ ký HMAC-SHA512 với khóa bí mật (`HashSecret`), cả hai phía (Website và VNPAY) có thể độc lập đối chiếu để chứng thực gói tin là hợp lệ.

### 3. WHEN (Khi nào dùng Callback và khi nào dùng IPN?)
| Tiêu chí | Callback (Return URL) | IPN (Instant Payment Notification) |
| :--- | :--- | :--- |
| **Kênh giao tiếp** | Front-channel (qua trình duyệt khách hàng) | Back-channel (Server-to-Server) |
| **Thời điểm kích hoạt** | Khi khách hoàn tất thao tác trên cổng VNPAY và trình duyệt chuyển hướng về web | Máy chủ VNPAY gửi ngầm một gói tin HTTP Request độc lập sang máy chủ website |
| **Mục đích** | **Chỉ dùng để hiển thị kết quả cho khách hàng** | **Cập nhật dữ liệu chính thức:** Lưu DB, xuất hóa đơn, trừ tồn kho |
| **Tính sẵn sàng** | Phụ thuộc vào người dùng (có thể mất mạng, tắt trình duyệt đột ngột) | Độc lập hoàn toàn với người dùng, có cơ chế gửi lại tự động nếu mạng chập chờn |

### 4. HOW (Thuật toán HMAC-SHA512 hoạt động như thế nào?)
- **Chiều đi (Build Payment URL):**
  1. Tập hợp các tham số (`vnp_Amount`, `vnp_TxnRef`, `vnp_OrderInfo`,...).
  2. Bỏ các tham số rỗng và **sắp xếp theo thứ tự bảng chữ cái A-Z**.
  3. Mã hóa URL-encoded và ghép thành chuỗi truy vấn chuẩn (`query_string`).
  4. Băm chuỗi dữ liệu với `HashSecret` bằng thuật toán `HMAC-SHA512` để sinh ra `vnp_SecureHash` gửi kèm lên VNPAY.
- **Chiều về (Validate Response):**
  1. Tách tham số `vnp_SecureHash` nhận được ra khỏi dữ liệu.
  2. Lấy toàn bộ tham số còn lại bắt đầu bằng `vnp_`, sắp xếp theo thứ tự A-Z và tạo chuỗi băm tương tự như lúc gửi đi.
  3. Tự tính toán mã băm mới và so sánh với `vnp_SecureHash` gửi về: nếu trùng khớp thì chấp nhận giao dịch, nếu sai lệch thì từ chối.

---

## 📁 CẤU TRÚC THƯ MỤC DỰ ÁN

```text
vnpay-sandbox-python/
│
├── config.py            # Chứa Terminal ID & Hash Secret cá nhân của từng bạn
├── vnpay.py             # Logic mã hóa HMAC-SHA512 & build URL VNPAY
├── main.py              # Server FastAPI định tuyến và xử lý các API endpoints
├── templates/
│   ├── index.html       # Giao diện đặt hàng chuẩn Store (VNStore)
│   └── result.html      # Giao diện hiển thị hóa đơn & đối soát chữ ký số
├── requirements.txt     # Danh sách thư viện phụ thuộc
└── README.md            # Tài liệu báo cáo seminar
```