"""Seminar demo: Payment request + Return URL + IPN + verification/SQLite."""
import os
import secrets
import sqlite3
from contextlib import asynccontextmanager, closing
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, ConfigDict

import config
from vnpay import VNPay

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv('DB_PATH', str(BASE_DIR / 'orders.db')))
VN_TZ = timezone(timedelta(hours=7))
DEMO_AMOUNT_VND = 50_000  # Giá trị đơn hàng chỉ do server quyết định.

vnpay_service = VNPay(
    tmn_code=config.VNPAY_TMN_CODE,
    hash_secret=config.VNPAY_HASH_SECRET,
    payment_url=config.VNPAY_PAYMENT_URL,
    return_url=config.VNPAY_RETURN_URL,
)


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(DB_PATH)) as db:
        db.execute('''CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY,
            amount_vnd INTEGER NOT NULL CHECK (amount_vnd > 0),
            status TEXT NOT NULL DEFAULT 'PENDING',
            created_at TEXT NOT NULL,
            response_code TEXT,
            transaction_status TEXT,
            vnp_transaction_no TEXT
        )''')
        db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title='VNPAY Sandbox Seminar (Request / Return / IPN)', lifespan=lifespan)


class PaymentPayload(BaseModel):
    # Chỉ cho chọn kênh; không nhận order_id/amount từ trình duyệt.
    model_config = ConfigDict(extra='forbid')
    bank_code: Literal['', 'NCB'] = 'NCB'


def read_order(order_id: str):
    with closing(sqlite3.connect(DB_PATH)) as db:
        db.row_factory = sqlite3.Row
        result = db.execute('SELECT * FROM orders WHERE order_id=?', (order_id,)).fetchone()
        return dict(result) if result else None


def parse_query(request: Request) -> dict | None:
    # Không cho phép key lặp gây sai khác trong cách diễn giải chữ ký.
    fields = list(request.query_params.multi_items())
    if len(fields) != len({k for k, _ in fields}):
        return None
    return dict(fields)


def check_return_fields(params: dict) -> dict:
    """Xác minh thông tin trình duyệt nhận được, KHÔNG cập nhật CSDL ở đây."""
    signed = vnpay_service.validate_response(params)
    order_id = params.get('vnp_TxnRef', '')
    order = read_order(order_id) if order_id else None
    merchant_matches = params.get('vnp_TmnCode') == config.VNPAY_TMN_CODE
    try:
        amount_matches = bool(order and int(params.get('vnp_Amount', '-1')) == order['amount_vnd'] * 100)
    except (TypeError, ValueError):
        amount_matches = False
    gateway_success = (params.get('vnp_ResponseCode') == '00'
                       and params.get('vnp_TransactionStatus') == '00')
    valid = signed and bool(order) and amount_matches and merchant_matches
    status = order['status'] if valid else 'UNVERIFIED'
    return {
        'is_valid': valid,  # Dữ liệu return được ký hợp lệ VÀ khớp với đơn hàng.
        'signature_valid': signed,
        'order_found': bool(order),
        'amount_matches': amount_matches,
        'merchant_matches': merchant_matches,
        'gateway_success': gateway_success,
        'response_code': params.get('vnp_ResponseCode'),
        'transaction_status': params.get('vnp_TransactionStatus'),
        'txn_ref': order_id,
        'order_status': status,  # Trạng thái backend, chỉ được IPN thay đổi.
        'is_paid': status == 'PAID',
        'amount_vnd': order['amount_vnd'] if valid else None,
        'vnp_transaction_no': order['vnp_transaction_no'] if valid else None,
    }


@app.get('/')
def home():
    return FileResponse(BASE_DIR / 'templates' / 'index.html')


@app.get('/payment/result')
def payment_result():
    return FileResponse(BASE_DIR / 'templates' / 'result.html')


@app.post('/api/payment/create-url')
def create_payment_url(payload: PaymentPayload, request: Request):
    if (not config.VNPAY_TMN_CODE or not config.VNPAY_HASH_SECRET
            or config.VNPAY_TMN_CODE.startswith('DIEN_')
            or config.VNPAY_HASH_SECRET.startswith('DIEN_')):
        raise HTTPException(status_code=400, detail='Chưa thiết lập VNPAY_TMN_CODE / VNPAY_HASH_SECRET trong .env')

    now = datetime.now(VN_TZ)
    date_str = now.strftime('%Y%m%d%H%M%S')
    order_id = f'HD{now:%Y%m%d%H%M%S}{secrets.token_hex(4).upper()}'
    with closing(sqlite3.connect(DB_PATH)) as db:
        db.execute('INSERT INTO orders (order_id, amount_vnd, status, created_at) VALUES (?, ?, ?, ?)',
                   (order_id, DEMO_AMOUNT_VND, 'PENDING', date_str))
        db.commit()

    client_ip = request.client.host if request.client else '127.0.0.1'
    params = {
        'vnp_Version': '2.1.0',
        'vnp_Command': 'pay',
        'vnp_TmnCode': config.VNPAY_TMN_CODE,
        'vnp_Amount': str(DEMO_AMOUNT_VND * 100),
        'vnp_CurrCode': 'VND',
        'vnp_TxnRef': order_id,
        'vnp_OrderInfo': f'Thanh toan don hang {order_id}',
        'vnp_OrderType': 'other',
        'vnp_Locale': 'vn',
        'vnp_ReturnUrl': config.VNPAY_RETURN_URL,
        'vnp_IpAddr': client_ip,
        'vnp_CreateDate': date_str,
        'vnp_ExpireDate': (now + timedelta(minutes=15)).strftime('%Y%m%d%H%M%S'),
    }
    if payload.bank_code:
        params['vnp_BankCode'] = payload.bank_code
    return {'order_id': order_id, 'amount_vnd': DEMO_AMOUNT_VND,
            'payment_url': vnpay_service.build_payment_url(params)}


@app.get('/api/payment/verify')
def verify_transaction(request: Request):
    params = parse_query(request)
    if params is None:
        raise HTTPException(status_code=400, detail='Không cho phép tham số trùng lặp')
    return check_return_fields(params)


@app.get('/api/orders/{order_id}')
def get_order(order_id: str):
    order = read_order(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail='Không tìm thấy đơn hàng')
    return {'order_id': order['order_id'], 'amount_vnd': order['amount_vnd'],
            'status': order['status'], 'response_code': order['response_code'],
            'transaction_status': order['transaction_status']}


@app.get('/api/payment/ipn')
def payment_ipn(request: Request):
    """Webhook GET server-to-server; JSON RspCode/Message theo tài liệu VNPAY."""
    params = parse_query(request)
    if params is None:
        return JSONResponse({'RspCode': '99', 'Message': 'Duplicate parameters'})
    if not vnpay_service.validate_response(params):
        return JSONResponse({'RspCode': '97', 'Message': 'Invalid signature'})
    if params.get('vnp_TmnCode') != config.VNPAY_TMN_CODE:
        return JSONResponse({'RspCode': '99', 'Message': 'Invalid merchant'})
    required = ('vnp_TxnRef', 'vnp_Amount', 'vnp_ResponseCode', 'vnp_TransactionStatus')
    if any(not params.get(field) for field in required):
        return JSONResponse({'RspCode': '99', 'Message': 'Missing required fields'})
    try:
        received_amount = int(params['vnp_Amount'])
    except ValueError:
        return JSONResponse({'RspCode': '04', 'Message': 'Invalid amount'})

    try:
        # BEGIN IMMEDIATE: khóa ghi để hai IPN đồng thời không cùng cập nhật một đơn.
        with closing(sqlite3.connect(DB_PATH, timeout=10)) as db:
            db.row_factory = sqlite3.Row
            db.execute('BEGIN IMMEDIATE')
            order = db.execute('SELECT * FROM orders WHERE order_id=?', (params['vnp_TxnRef'],)).fetchone()
            if not order:
                db.rollback()
                return JSONResponse({'RspCode': '01', 'Message': 'Order not found'})
            if received_amount != order['amount_vnd'] * 100:
                db.rollback()
                return JSONResponse({'RspCode': '04', 'Message': 'Invalid amount'})
            if order['status'] != 'PENDING':
                db.rollback()
                return JSONResponse({'RspCode': '02', 'Message': 'Order already confirmed'})

            # Nếu cổng chưa có trạng thái cuối, giữ PENDING và đề nghị retry.
            if params['vnp_TransactionStatus'] == '01':
                db.rollback()
                return JSONResponse({'RspCode': '99', 'Message': 'Transaction not final'})

            if params['vnp_ResponseCode'] == '00' and params['vnp_TransactionStatus'] == '00':
                new_status = 'PAID'
            elif params['vnp_TransactionStatus'] in ('04', '07'):
                new_status = 'REVIEW'  # Đảo / nghi ngờ gian lận: không coi là PAID.
            else:
                new_status = 'FAILED'

            db.execute('''UPDATE orders SET status=?, response_code=?,
                          transaction_status=?, vnp_transaction_no=? WHERE order_id=?''',
                       (new_status, params['vnp_ResponseCode'],
                        params['vnp_TransactionStatus'], params.get('vnp_TransactionNo', ''),
                        params['vnp_TxnRef']))
            db.commit()
        return JSONResponse({'RspCode': '00', 'Message': 'Confirm Success'})
    except sqlite3.Error:
        # Không in chuỗi bí mật / dữ liệu nhạy cảm ra màn hình.
        return JSONResponse({'RspCode': '99', 'Message': 'Database error'})
