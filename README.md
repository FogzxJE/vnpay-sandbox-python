> **CHẠY ONE CLICK TRÊN WINDOWS & MAC:** Trên Windows nhấp đúp `START_DEMO.bat`; trên macOS nhấp đúp `START_DEMO.command`. Có cả bản HTTPS (`START_PUBLIC_DEMO.*`), test tự động (`RUN_TESTS.*`) và nút dừng Mac (`STOP_DEMO.command`). Xem **[HUONG_DAN_ONE_CLICK.md](HUONG_DAN_ONE_CLICK.md)** để biết điều kiện cài Python, cấu hình ngrok và IPN.

# Chạy nhanh bằng một cú nhấp (Windows)

- **`START_DEMO.bat`**: chạy FastAPI và mở website local (an toàn, không công khai Internet).
- **`START_PUBLIC_DEMO.bat`**: làm tương tự nhưng bật ngrok nếu máy đã cấu hình; tự dùng URL HTTPS ngrok trong Return URL khi khởi tạo server mới.
- **`RUN_TESTS.bat`**: xem toàn bộ bài kiểm thử tự động.

Xem hướng dẫn **`HUONG_DAN_ONE_CLICK.md`**. Cần Python 3.10+; lần đầu chạy cần Internet để cài thư viện. Bản ZIP không kèm Hash Secret; phải tự cấu hình `.env` hợp lệ để thực hiện giao dịch VNPAY Sandbox thật. VNPAY cần được đăng ký URL IPN riêng để gửi webhook về máy.

---

# Seminar: Tích hợp VNPAY Sandbox — Payment Request, Return URL, IPN, Verification

> **Bản dùng để thực hành và học tập (FastAPI + SQLite)**. Không sử dụng cho tiền thật hoặc production nếu chưa được kiểm thử bảo mật, triển khai QueryDr/reconciliation, kiểm soát vận hành và đánh giá tuân thủ.

## 1. What — Why — How — When

- **WHAT:** Tích hợp cổng VNPAY Sandbox qua API tạo URL thanh toán, Return URL, IPN và truy vấn trạng thái đơn hàng.
- **WHY:** Kiểm thử luồng từ đơn hàng đến thanh toán, đảm bảo thông điệp không bị sửa (HMAC-SHA512) và không nhầm `checksum hợp lệ` với `đã thanh toán`.
- **HOW:** Backend sinh mã đơn, lấy số tiền từ server, ghi `PENDING` vào SQLite, ký URL thanh toán; khi VNPAY trả về, kiểm tra HMAC + merchant + đơn hàng + số tiền. IPN mới được quyền thay đổi trạng thái đơn.
- **WHEN:** Return URL = người mua quay về bằng trình duyệt, dùng cho hiển thị; IPN = VNPAY gọi tới server qua HTTPS, xử lý nghiệp vụ độc lập với trình duyệt. Có thể dùng QueryDr để đối soát giao dịch chưa chắc chắn (chưa tích hợp trong phiên bản demo này).

Tài liệu VNPAY: <https://sandbox.vnpayment.vn/apis/docs/thanh-toan-pay/pay.html> và <https://sandbox.vnpayment.vn/apis/docs/truy-van-hoan-tien/querydr%26refund.html>.

## 2. Cấu trúc dự án

```text
vnpay_seminar_hoan_thien/
├── main.py                # API FastAPI, SQLite, Return verify, IPN
├── vnpay.py               # Canonical URL và HMAC-SHA512
├── config.py              # Đọc cấu hình môi trường (.env)
├── .env.example           # Mẫu cấu hình không chứa mật khẩu thật
├── .gitignore             # Chặn đăng bí mật/database lên GitHub
├── requirements.txt
├── simulate_ipn.py        # Mô phỏng IPN CÓ KÝ, local only
├── tests/test_payment.py  # 11 ca test (không cần gọi VNPAY)
└── templates/
    ├── index.html         # Giữ giao diện VNStore ban đầu
    └── result.html        # Hiển thị từ backend, không tin URL ngay
```

## 3. Chuẩn bị môi trường — Windows PowerShell (khuyến nghị cho thực hành tại lớp)

**Yêu cầu:** Windows 10/11, Python 3.10 trở lên, `py` launcher, trình duyệt Chrome/Edge, Internet nếu muốn thanh toán qua cổng thật. `Git` là tùy chọn (có thể Download ZIP). Không cần cài Node.js hay MySQL. SQLite có sẵn trong Python.

```powershell
# 1. Mở PowerShell ngay trong thư mục dự án đã tải về
py -3 --version
# 2. Tạo môi trường riêng
py -3 -m venv .venv
# 3. Cài dependencies không cần kích hoạt môi trường
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
# 4. Sao chép mẫu biến môi trường
Copy-Item .env.example .env
```

Mở file `.env` bằng Notepad/VS Code, thay **hai giá trị `DIEN_...`** bằng TMN Code và Hash Secret Sandbox của chính bạn. Ví dụ `VNPAY_TMN_CODE=ABCDEFGH` chỉ là ký hiệu minh họa. **Tuyệt đối không đăng Hash Secret lên GitHub, slides, video, hoặc ảnh chụp màn hình.** Nếu từng công bố một Hash Secret, hãy yêu cầu VNPAY cấp/đổi secret trước khi dùng tiếp.

```powershell
# 5. Kiểm tra tự động (offline) — 11 test
.\.venv\Scripts\python.exe -m pytest -q
# 6. Chạy web (nếu port 8000 rảnh)
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
```

Truy cập:
- Trang chủ: <http://127.0.0.1:8000/>
- Trang tài liệu API: <http://127.0.0.1:8000/docs>
- IPN endpoint: <http://127.0.0.1:8000/api/payment/ipn> (không cập nhật khi truy cập trống hoặc không có chữ ký)

**macOS/Linux:** thay dòng khởi tạo Python bằng `python3 -m venv .venv`, cài bằng `.venv/bin/python -m pip install -r requirements.txt`, kiểm thử bằng `.venv/bin/python -m pytest -q` và chạy bằng `.venv/bin/python -m uvicorn main:app --reload --port 8000`. Tạo `.env` bằng `cp .env.example .env`.

### Sự cố thường gặp

| Hiện tượng | Cách xử lý |
|---|---|
| `py` không có lệnh | Cài Python chính thức và bật tùy chọn PATH hoặc dùng `python -m ...` |
| `ModuleNotFoundError` | Chạy chính xác Python bên trong `.venv` như các lệnh trên |
| `Address already in use`, port 8000 đang bận | Dừng server đang chiếm port; không đổi port mà quên sửa Return URL |
| `GET /` báo 404/500 | Kiểm tra `templates/index.html` và `templates/result.html` thực sự nằm trong thư mục `templates/` |
| `400 Chưa thiết lập...` | Điền `.env` bằng credentials Sandbox được cấp |
| VNPAY từ chối yêu cầu hoặc báo checksum | Kiểm tra TMN Code/Hash Secret đúng cặp; `vnp_ReturnUrl`; đồng hồ máy đúng giờ GMT+7; tài khoản còn hiệu lực |
| Frontend tải thiếu icon/style | Internet/CDN của Bootstrap và FontAwesome đang bị chặn; backend vẫn xử lý được |
| Thanh toán về trang kết quả nhưng hiển thị `PENDING` | Nếu chưa cấu hình HTTPS IPN công khai thì đây là điều bình thường, **không phải đã thanh toán được xác nhận** |

## 4. Demo Offline: KHÔNG cần Internet hay thanh toán qua VNPAY

**Mục tiêu:** để cả lớp chạy được ngay, kể cả IPN chưa được VNPAY cấu hình.

**Cách A — pytest:** chạy `.\.venv\Scripts\python.exe -m pytest -v`. Kiểm tra 11 ca: trang chủ, tạo đơn, cấm sửa giá, Return không đánh dấu PAID, IPN thành công, IPN lặp, HMAC sai, tiền sai, mã đơn không tồn tại, merchant sai, giao dịch thất bại, pending và tham số URL lặp (xem `tests/test_payment.py`; bài test gộp một số tình huống).

**Cách B — quan sát SQLite chuyển trạng thái (PowerShell):**

1. Mở server FastAPI ở một terminal.
2. Mở terminal PowerShell thứ hai, lấy 1 đơn mới và mã đơn:

```powershell
$resp = Invoke-RestMethod -Uri http://127.0.0.1:8000/api/payment/create-url -Method POST -ContentType 'application/json' -Body '{"bank_code":"NCB"}'
$resp | Select-Object order_id,amount_vnd
$oid = $resp.order_id
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/orders/$oid"
```

Trạng thái ban đầu là `PENDING`. Sau đó gửi IPN mô phỏng đã ký:

```powershell
.\.venv\Scripts\python.exe simulate_ipn.py $oid --status success
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/orders/$oid"
```

Kỳ vọng: IPN nhận `RspCode=00`, SQLite đổi `PENDING -> PAID`. Chạy lại **cùng lệnh**, IPN phải trả `RspCode=02` và không ghi trùng. Đổi `--status cancel`, `review`, `pending` trên **đơn mới** để xem các trạng thái khác.

> IPN mô phỏng **không phải** thông báo của VNPAY thật và không chứng minh đã phát sinh giao dịch. Bản demo dùng Hash Secret cục bộ để giải thích quy trình xác minh chữ ký và trạng thái.

## 5. Demo Online: VNPAY Sandbox thực tế

1. Tạo tài khoản/credential Sandbox trên <https://sandbox.vnpayment.vn/devreg/>. **Chuẩn bị trước buổi học**, vì đăng ký nhận email/xác nhận có thể mất thời gian.
2. Điền `.env` với credentials thực được cấp (không dùng các giá trị placeholder) và chạy server.
3. Nhấn **Tiến hành thanh toán** trên `http://127.0.0.1:8000/`. Backend ghi đơn `PENDING`, trả URL HMAC; browser chuyển sang VNPAY.
4. Sử dụng thẻ test NCB từ tài liệu chính thức: ngân hàng NCB, số thẻ `9704198526191432198`, tên `NGUYEN VAN A`, ngày phát hành `07/15`, OTP `123456`. Xác nhận lại trên tài liệu VNPAY nếu danh sách thẻ thử nghiệm thay đổi: <https://sandbox.vnpayment.vn/apis/vnpay-demo/>.
5. Browser quay về trang Return URL. Nếu VNPAY chưa được cấu hình IPN HTTPS thì kết quả sẽ ghi **chờ IPN**, dù Return URL có HMAC hợp lệ, và đây là thiết kế đúng.

### Bật IPN thật (cần cấu hình với VNPAY; không tự động hoạt động)

1. Chạy FastAPI local ở port 8000.
2. Dùng công cụ tunnel HTTPS như ngrok/Cloudflare Tunnel theo tài khoản của bạn, trỏ public HTTPS tới `http://127.0.0.1:8000`. Ví dụ công cụ ngrok nếu đã cài: `ngrok http 8000`.
3. Lấy hostname HTTPS do tunnel cấp. Địa chỉ IPN phải là `https://<hostname>/api/payment/ipn`. **Không** dùng `localhost` hoặc `127.0.0.1` làm địa chỉ IPN với VNPAY; server VNPAY không truy cập máy cá nhân qua tên đó.
4. Khai báo/xác nhận URL IPN với VNPAY theo quy trình cấu hình Sandbox mà tài khoản merchant được cấp. Tài liệu yêu cầu cung cấp IPN URL cho VNPAY; **việc mở tunnel không tự đăng ký IPN với VNPAY**.
5. Thực hiện đơn mới. Xem log `GET /api/payment/ipn?...` trên terminal, kiểm tra `RspCode` và truy cập `/api/orders/<mã đơn>` để kiểm tra trạng thái DB. Không quay màn hình có lộ secret hoặc toàn bộ dữ liệu giao dịch nhạy cảm.
6. Nếu màn hình Return về trước IPN, giao diện hiển thị `PENDING` và kiểm tra lại backend trong khoảng 30 giây; không tự báo thành công.

Lưu ý: Demo offline là phương án dự phòng nếu đường truyền/tunnel hoặc việc đăng ký IPN với VNPAY bị gián đoạn.

## 6. Những điểm kỹ thuật giảng viên có thể hỏi

| Câu hỏi | Câu trả lời kỹ thuật |
|---|---|
| HMAC đúng có chắc thanh toán thành công không? | Không. HMAC chỉ xác minh thông điệp và tính toàn vẹn; còn phải kiểm tra đơn hàng, merchant, số tiền, response code và transaction status, IPN và DB. |
| Vì sao dùng `vnp_Amount = amount * 100`? | Quy ước API của VNPAY; 50.000 VNĐ được gửi là `5000000`. |
| Vì sao Return URL không cập nhật DB? | Đây là front-channel; trình duyệt có thể bị tắt hoặc tham số URL có thể bị sử dụng lại. Server nhận IPN để xử lý trạng thái độc lập với browser. |
| IPN đến 2 lần thì sao? | DB chỉ xử lý trạng thái `PENDING` lần đầu. Các lần sau trả `RspCode=02` (đã xử lý). |
| Nếu số tiền sai hoặc signature sai? | Không cập nhật DB; lần lượt phản hồi IPN `04` hoặc `97`. |
| Vì sao cần SQLite? | Demo trạng thái thật, không phải hiển thị giả trên trình duyệt. Trên production cần DB, audit log, quản trị khóa, HTTPS, reconciliation... |
| Nếu IPN thất lạc? | VNPAY có retry tùy mã RspCode; với tình huống quá thời gian/chưa rõ trạng thái cần QueryDr và đối soát. QueryDr **chưa được lập trình** trong demo này. |

## 7. Mô hình dữ liệu & endpoints

Bảng `orders` có `order_id`, `amount_vnd`, `status` (`PENDING`, `PAID`, `FAILED`, `REVIEW`), `created_at`, `response_code`, `transaction_status`, `vnp_transaction_no`. Database SQLite sinh tự động ở `orders.db` và đã được `.gitignore` loại bỏ khỏi Git.

| Method | Endpoint | Vai trò |
|---|---|---|
| GET | `/` | Giao diện VNStore |
| POST | `/api/payment/create-url` | Tạo đơn ở backend, ký URL |
| GET | `/payment/result` | Hiển thị UI Return URL |
| GET | `/api/payment/verify` | Kiểm tra dữ liệu Return, **không đổi trạng thái DB** |
| GET | `/api/payment/ipn` | Nhận IPN, xác thực, ghi DB, trả RspCode JSON |
| GET | `/api/orders/{order_id}` | Xem trạng thái đã ghi trong DB |
| GET | `/docs` | Swagger API docs |

**Về bảo mật:** `hmac.compare_digest()` tránh so sánh chuỗi chữ ký theo cách thông thường; kiểm tra tham số URL lặp; đơn hàng và tiền lấy từ server; SQL parameterized; SQLite transaction (`BEGIN IMMEDIATE`) ngăn đua ghi trạng thái. Trên môi trường production còn phải có xác thực, chống lạm dụng, HTTPS, kiểm tra yêu cầu đến, logs, giới hạn tốc độ, lưu lịch sử và đối soát.

## 8. Chấm phần seminar / vật phẩm bàn giao

- [ ] Slide có WHAT – WHY – HOW – WHEN, kiến trúc request → VNPAY → Return/IPN → SQLite.
- [ ] Slide nêu khác biệt checksum / kết quả gateway / trạng thái đơn hàng backend.
- [ ] Trình chiếu code `vnpay.py` (HMAC), `main.py` (tạo URL, IPN), `tests/test_payment.py`.
- [ ] Demo ít nhất 4 trường hợp: thành công, sai chữ ký, sai số tiền, callback lặp.
- [ ] Chia sẻ GitHub/ZIP, README, `.env.example`, toàn bộ file templates và test để cả lớp dùng được.
- [ ] Video bài giảng >= 20 phút (xem hướng dẫn Seminar), quay đủ terminal + browser + giải thích từng ca.
- [ ] Chia sẻ tài liệu kỹ thuật trước 3 ngày nếu có thể; kiểm tra từ cửa sổ ẩn danh để bảo đảm repo tải được.
- [ ] Không xuất bản `.env`, database có dữ liệu giao dịch, secret, hoặc OTP thật.

---

**Giới hạn phạm vi có chủ ý:** Đây là bản tích hợp quy trình PAY + Return + IPN + đối chiếu đơn hàng và mô phỏng offline. Không triển khai QueryDr và refund. Để mở rộng thành hệ thống production, cần xây dựng QueryDr, lịch đối soát, xử lý timeout, logging, bảo vệ endpoint và kiểm thử với VNPAY thực.
