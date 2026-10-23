#!/bin/bash
# Shared macOS startup: Finder .command entries invoke this script.
# Compatible with the Bash 3.2 version included with macOS.
set -u

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT" || exit 1
# Finder/Terminal can have a minimal PATH; include both Apple Silicon and Intel Homebrew.
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
MODE="${1:---local}"

pause_on_failure() {
  printf '\nNhấn Enter để đóng cửa sổ... '
  read -r _unused || true
}
fail() {
  printf '\n[LOI] %s\n' "$1" >&2
  pause_on_failure
  exit 1
}

printf '\n========================================================\n'
printf '  VNPAY SANDBOX - ONE CLICK macOS\n'
printf '  Chế độ: %s\n' "$MODE"
printf '========================================================\n\n'

[ -f "main.py" ] || fail "Không thấy main.py. Giữ các file .command cạnh main.py trong thư mục dự án."

if [ "$MODE" = "--stop" ]; then
  if [ -x ".venv/bin/python" ]; then
    ".venv/bin/python" "one_click_launcher.py" --stop || fail "Không dừng được demo tự động. Xem thông báo phía trên."
  else
    printf '[INFO] Không có môi trường ảo của Mac; không có tiến trình cần dừng từ bộ khởi động này.\n'
  fi
  printf '\nHoàn tất. Bạn có thể đóng cửa sổ.\n'
  exit 0
fi

# Never bundle any live credentials. Create a placeholder .env once.
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
  cp ".env.example" ".env" || fail "Không tạo được .env."
  printf '[INFO] Đã tạo .env mẫu. Demo thanh toán Sandbox thật cần credential hợp lệ.\n'
fi

get_python() {
  for executable in python3 python3.13 python3.12 python3.11 python3.10 python; do
    if command -v "$executable" >/dev/null 2>&1; then
      if "$executable" -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)' >/dev/null 2>&1; then
        printf '%s' "$executable"
        return 0
      fi
    fi
  done
  return 1
}

if [ ! -x ".venv/bin/python" ]; then
  if [ -d ".venv" ]; then
    fail "Có .venv không phải môi trường Mac (ví dụ copy từ Windows). Đổi tên/xóa .venv rồi chạy lại. KHÔNG cần xóa file code."
  fi
  PYTHON_BIN="$(get_python)" || fail "Cần cài Python 3.10+. Xem https://www.python.org/downloads/macos/ rồi mở Terminal mới."
  printf '[1/3] Đang tạo .venv với %s...\n' "$PYTHON_BIN"
  "$PYTHON_BIN" -m venv .venv || fail "Không tạo được môi trường .venv. Kiểm tra Python và quyền ghi thư mục."
fi

PY="${ROOT}/.venv/bin/python"
"$PY" -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)' || fail "Python trong .venv quá cũ. Đổi tên .venv rồi chạy lại."

printf '[2/3] Đang kiểm tra thư viện...\n'
if ! "$PY" -c 'import fastapi, uvicorn, dotenv, httpx, pytest' >/dev/null 2>&1; then
  printf '[INFO] Cài đặt từ requirements.txt (lần đầu cần Internet).\n'
  "$PY" -m pip install -r requirements.txt || fail "Cài thư viện thất bại. Kiểm tra Internet và thông báo pip ở trên."
fi

if [ "$MODE" = "--tests" ]; then
  printf '[3/3] Chạy kiểm thử...\n'
  "$PY" -m pytest -v
  code=$?
  if [ "$code" -ne 0 ]; then
    fail "Có bài kiểm thử không đạt (exit: $code)."
  fi
  printf '\n[OK] Đã chạy xong bộ kiểm thử.\n'
  printf 'Nhấn Enter để đóng cửa sổ... '
  read -r _unused || true
  exit 0
fi

[ "$MODE" = "--local" ] || [ "$MODE" = "--public" ] || fail "Chế độ không hỗ trợ: $MODE"
printf '[3/3] Khởi động VNStore...\n'
if [ "$MODE" = "--public" ]; then
  "$PY" "one_click_launcher.py" --ngrok ${VNPAY_DEMO_NO_BROWSER:+--no-browser} || fail "Không mở được demo. Xem .demo-uvicorn.log hoặc thông báo phía trên."
else
  "$PY" "one_click_launcher.py" ${VNPAY_DEMO_NO_BROWSER:+--no-browser} || fail "Không mở được demo. Xem .demo-uvicorn.log hoặc thông báo phía trên."
fi

printf '\n[OK] Đã mở VNStore. Có thể đóng cửa sổ này.\n'
printf 'Để dừng FastAPI/ngrok do launcher tạo, nhấp đúp STOP_DEMO.command.\n'
