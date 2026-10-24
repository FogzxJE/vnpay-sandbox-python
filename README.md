# VNStore – Tích hợp thanh toán VNPAY Sandbox (FastAPI)

> **Dự án Seminar:** Payment Request · Return URL · IPN Callback · Transaction Verification  
> **Hệ điều hành:** Windows và macOS · **Backend:** Python/FastAPI · **Lưu dữ liệu:** SQLite  
> **Môi trường thanh toán:** **VNPAY Sandbox dùng thẻ thử nghiệm**, không phải môi trường tiền thật.

## 1. Chạy nhanh (One-Click)

**Cài Python 3.10 trở lên trước khi chạy.** Nếu dùng bản HTTPS, cần cài ngrok và cấu hình Authtoken trên máy một lần. Lần đầu máy cần Internet để cài thư viện Python. Bạn cần **tạo `.env` và điền thông tin Sandbox trước khi demo thanh toán**, không đưa khóa bí mật lên GitHub.

| Việc cần làm | Windows | macOS |
| --- | --- | --- |
| Mở website tại localhost | Nhấp đúp `launcher/START_DEMO.bat` | Nhấp đúp `launcher/START_DEMO.command` |
| Mở website qua HTTPS ngrok | Nhấp đúp `launcher/START_PUBLIC_DEMO.bat` | Nhấp đúp `launcher/START_PUBLIC_DEMO.command` |
| Dừng tiến trình do One-Click chạy | `launcher/STOP_DEMO.bat` | `launcher/STOP_DEMO.command` |

- Local: <http://127.0.0.1:8000/>
- FastAPI Swagger: <http://127.0.0.1:8000/docs>
- Ngrok Inspector khi tunnel hoạt động: <http://127.0.0.1:4040/>
- **Tài liệu hướng dẫn có hình, từng bước:** [`docs/Huong_Dan_One_Click_VNPAY_Windows_Mac.docx`](docs/Huong_Dan_One_Click_VNPAY_Windows_Mac.docx)

**Lưu ý:** Đây là *One-Click sau khi chuẩn bị lần đầu*, không phải ứng dụng độc lập chạy trên máy chưa cài Python. Các file `RUN_TESTS.*` và thư mục `tests/` **không có trong phiên bản hiện tại**.

## 2. Cấu trúc thư mục THỰC TẾ

```text
vnpay-sandbox-python/
├── launcher/
│   ├── START_DEMO.bat                  # Windows: mở website local
│   ├── START_PUBLIC_DEMO.bat           # Windows: mở website + ngrok
│   ├── STOP_DEMO.bat                   # Windows: dừng demo
│   ├── START_DEMO.command              # macOS: mở website local
│   ├── START_PUBLIC_DEMO.command       # macOS: mở website + ngrok
│   └── STOP_DEMO.command               # macOS: dừng demo
├── templates/
│   ├── index.html                      # Trang đặt hàng VNStore
│   └── result.html                     # Trang kết quả, chờ trạng thái IPN
├── docs/
│   └── Huong_Dan_One_Click_VNPAY_Windows_Mac.docx
├── main.py                             # FastAPI, tạo đơn, Return, IPN, SQLite
├── vnpay.py                            # Chuẩn hóa tham số và ký/kiểm HMAC-SHA512
├── config.py                           # Đọc cấu hình từ .env
├── simulate_ipn.py                     # Giả lập IPN để kiểm thử nghiệp vụ
├── one_click_launcher.py               # Khởi động backend/ngrok/trình duyệt
├── mac_start.sh                        # Script hỗ trợ launcher macOS
├── stop_demo_windows.ps1               # Dừng tiến trình trên Windows
├── requirements.txt                    # Các thư viện Python cần cài
├── .env.example                        # Mẫu biến môi trường, an toàn để chia sẻ
├── .gitignore                           # Loại file bí mật và file tạo lúc chạy
├── .gitattributes                       # Đảm bảo line ending LF cho macOS
└── README.md                           # Tài liệu này
```

**Những file có thể sinh ra trên máy bạn nhưng KHÔNG được nộp/đẩy lên GitHub:** `.env`, `.venv/`, `orders.db`, `.demo-*.pid`, `.demo-*.log`, `.git/`, `__pycache__/`.

## 3. Chuẩn bị tài khoản ngrok → VNPAY (không cần START rồi STOP giữa chừng)

1. Cài Python: [Windows](https://www.python.org/downloads/windows/) hoặc [macOS](https://www.python.org/downloads/macos/).
2. Đăng ký ngrok tại <https://dashboard.ngrok.com/signup>. Vào [Domains](https://dashboard.ngrok.com/domains), sao chép tên miền HTTPS được tài khoản cấp. Ví dụ dạng `https://TEN-MIEN.ngrok-free.dev`. **Không tự bịa tên miền**.
3. Cài [ngrok Windows](https://ngrok.com/download/windows) hoặc [ngrok macOS](https://ngrok.com/download/mac-os); lấy Authtoken tại <https://dashboard.ngrok.com/get-started/your-authtoken>. Chạy **một lần trên mỗi máy**:

   ```bash
   ngrok config add-authtoken "AUTHTOKEN_CUA_BAN"
   ```

4. Đăng ký VNPAY Sandbox tại <https://sandbox.vnpayment.vn/devreg/>. Nếu biểu mẫu chấp nhận, nhập đúng **URL website ngrok bạn quản lý**. Nhận **TMN Code** và **Hash Secret** qua kênh do VNPAY cung cấp. Nếu ngrok domain không được chấp nhận, hỏi VNPAY về URL hợp lệ; không sử dụng website của người khác.
5. Tạo `.env` từ `.env.example` **trước khi START**:

   - Windows PowerShell: `Copy-Item .env.example .env`
   - macOS Terminal: `cp .env.example .env`

   Mở `.env` và điền:

   ```dotenv
   VNPAY_TMN_CODE=MA_DO_VNPAY_CAP
   VNPAY_HASH_SECRET=KHOA_BI_MAT_DO_VNPAY_CAP
   VNPAY_RETURN_URL=https://TEN-MIEN.ngrok-free.dev/payment/result
   ```

6. Chỉ khi đã cấu hình xong, mở `launcher/START_PUBLIC_DEMO.bat` (Windows) hoặc `launcher/START_PUBLIC_DEMO.command` (Mac). Launcher sẽ sử dụng HTTPS URL do ngrok **thực tế** cung cấp cho phiên backend mới. Kiểm tra URL đang chạy có khớp website bạn định sử dụng hay không.

**Bảo mật:** Không gửi `.env`, ngrok Authtoken, Hash Secret hay Git history có thông tin nhạy cảm cho người khác. Nếu khóa từng bị đưa lên GitHub, cần yêu cầu VNPAY **đổi/vô hiệu hóa khóa cũ**. Không tự đặt chuỗi Hash Secret khác với khóa bên VNPAY.

## 4. Demo thanh toán VNPAY Sandbox

1. Mở website VNStore từ HTTPS URL được One-Click/ngrok hiển thị; chọn ngân hàng **NCB** và nhấn **Tiến hành thanh toán**.
2. Backend tạo mã đơn hàng mới, lưu đơn **50.000 VNĐ** với trạng thái `PENDING` vào `orders.db`, rồi tạo Payment URL có chữ ký HMAC-SHA512.
3. Trình duyệt chuyển sang VNPAY Sandbox. Sử dụng **thẻ test do VNPAY công bố** tại <https://sandbox.vnpayment.vn/apis/vnpay-demo/> (không dùng thẻ/tài khoản ngân hàng thật).
4. VNPAY chuyển về `/payment/result`. Trang kết quả kiểm tra chữ ký HMAC, merchant, mã đơn và số tiền.
5. Nếu hiển thị **“Đang chờ xác nhận IPN”**, tức backend chưa xác nhận đơn hàng `PAID`, dù Return URL hợp lệ. Đây **không phải lỗi giao diện**.

### Phân biệt Return URL và IPN

| Thành phần | Mục đích |
| --- | --- |
| `https://TEN-MIEN.ngrok-free.dev/payment/result` | Trình duyệt quay về và hiển thị kết quả |
| `https://TEN-MIEN.ngrok-free.dev/api/payment/ipn` | VNPAY gọi server-to-server, backend xác minh và cập nhật CSDL |

**IPN thật chỉ hoạt động khi URL HTTPS của bạn được VNPAY tiếp nhận/cấu hình.** Bật ngrok hoặc sửa `.env` **không tự đăng ký IPN**. Kiểm tra request `GET /api/payment/ipn` tại <http://127.0.0.1:4040/>. Các dòng `GET /api/orders/... 200 OK` chỉ là frontend đang hỏi trạng thái, **không phải IPN**.

### Mô phỏng IPN (phương án dự phòng cho Seminar)

Nếu chưa được VNPAY cấu hình IPN, hãy tạo **đơn thử nghiệm đang PENDING** rồi chạy lệnh tương ứng tại thư mục gốc dự án. Thay `MA_DON_HANG` bằng mã đơn thật từ website:

Windows PowerShell:
```powershell
.\.venv\Scripts\python.exe simulate_ipn.py MA_DON_HANG --status success
```

macOS Terminal:
```bash
./.venv/bin/python simulate_ipn.py MA_DON_HANG --status success
```

Nếu chữ ký, số tiền và mã đơn hợp lệ, trạng thái đơn thử nghiệm sẽ chuyển `PENDING` → `PAID`. **Đây là IPN tự mô phỏng, KHÔNG chứng minh VNPAY đã thanh toán hoặc gửi IPN thật.**

## 5. File code và API chính

| File / API | Chức năng |
| --- | --- |
| `templates/index.html` | Giao diện và lệnh `fetch()` gửi yêu cầu tạo thanh toán |
| `main.py` – `create_payment_url()` | Sinh mã đơn, lưu `PENDING`, tạo tham số thanh toán |
| `vnpay.py` – `canonical_query()`, `sign_params()` | Sắp xếp tham số và ký HMAC-SHA512 |
| `vnpay.py` – `validate_response()` | So sánh chữ ký bằng `hmac.compare_digest()` |
| `GET /api/payment/verify` | Xác minh dữ liệu Return; **không cập nhật trạng thái DB** |
| `GET /api/payment/ipn` | Xác minh IPN và cập nhật trạng thái đơn trong SQLite |
| `GET /api/orders/{order_id}` | Trả trạng thái đơn hàng để trang kết quả kiểm tra |
| `simulate_ipn.py` | Tạo IPN **mô phỏng** phục vụ kiểm thử trên máy |
| `one_click_launcher.py` | Tạo/kiểm tra backend, ngrok và mở trình duyệt |

`main.py` dùng SQLite với trạng thái `PENDING`, `PAID`, `FAILED`, `REVIEW`. IPN kiểm tra HMAC, TMN Code, mã đơn, số tiền và không xử lý hai lần đơn đã hoàn thành. Phiên bản Seminar **chưa tích hợp QueryDr, hoàn tiền, đối soát nâng cao** và không được xem là triển khai Production.

## 6. Sự cố thường gặp

| Hiện tượng | Cách xử lý |
| --- | --- |
| Máy khác báo đường dẫn Python của máy cũ | **Không sao chép `.venv`**. Xóa `.venv` được sao chép và để máy mới tự tạo lại |
| Không tìm thấy file One-Click | Mở **thư mục `launcher/`**, không tìm ở thư mục gốc |
| Mac báo không mở được `.command` | Kiểm tra file đáng tin cậy và cấp quyền: `chmod +x launcher/*.command mac_start.sh` trong Terminal tại thư mục gốc |
| Không có HTTPS URL | Kiểm tra `ngrok version`, Authtoken, mạng Internet và tunnel ngrok |
| `POST /api/payment/create-url` trả 400 | Kiểm tra TMN Code/Hash Secret hợp lệ trong `.env`, khởi động lại nếu vừa sửa cấu hình |
| `GET /favicon.ico` trả 404 | Chỉ thiếu biểu tượng tab; không ảnh hưởng thanh toán |
| Trả về website nhưng vẫn `PENDING` | Kiểm tra VNPAY đã cấu hình IPN chưa, xem ngrok Inspector, không gọi đó là thanh toán đã xác nhận |
| Cổng 8000 đang bận | Dừng server cũ trước khi chạy launcher mới |
| IPN mô phỏng báo thiếu `order_id` | Dùng mã đơn thực tế thay `MA_DON_HANG`; không nhập `$oid` nếu chưa gán biến trong PowerShell |

**macOS:** Dự án cần file `.command` có line ending **LF** và quyền thực thi. File `.gitattributes` giữ line ending đúng khi clone trên Windows/Mac. Nếu giải nén từ ZIP làm mất quyền thực thi, thực hiện `chmod +x launcher/*.command mac_start.sh` **một lần**. Để tránh lỗi cho người clone repo, người phát triển nên đưa quyền thực thi của `.command` vào Git (file mode `100755`).

## 7. Bàn giao Seminar

- Chia sẻ repository/ZIP **chỉ gồm mã nguồn và tài liệu**; không gồm `.git/`, `.env`, `.venv/`, cơ sở dữ liệu `orders.db` hoặc file PID/log.
- Nộp tài liệu [`docs/Huong_Dan_One_Click_VNPAY_Windows_Mac.docx`](docs/Huong_Dan_One_Click_VNPAY_Windows_Mac.docx) cùng slides và video seminar theo yêu cầu giảng viên.
- Chạy thử từ **một thư mục tải/clone mới trên máy khác** trước khi thuyết trình.

**Tài liệu kỹ thuật VNPAY:** [PAY / Return / IPN](https://sandbox.vnpayment.vn/apis/docs/thanh-toan-pay/pay.html).  
**Giới hạn:** Bài demo chỉ dùng Sandbox, cần cấu hình IPN thật riêng; không sử dụng trực tiếp cho giao dịch tiền thật.
