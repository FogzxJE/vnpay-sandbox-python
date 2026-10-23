"""Giả lập IPN có HMAC đúng để DEMO OFFLINE. KHÔNG phải phản hồi thật của VNPAY."""
import argparse
import json
from urllib.parse import urlencode
from urllib.request import urlopen

import config
from vnpay import VNPay

parser = argparse.ArgumentParser(description='Gửi IPN MÔ PHỎNG tới local server')
parser.add_argument('order_id', help='Mã HD... lấy từ vnp_TxnRef khi tạo đơn')
parser.add_argument('--status', choices=['success', 'cancel', 'review', 'pending'], default='success')
args = parser.parse_args()

if not config.VNPAY_HASH_SECRET or not config.VNPAY_TMN_CODE:
    parser.error('Tạo file .env với thông tin Sandbox trước khi chạy')

vnpay = VNPay(config.VNPAY_TMN_CODE, config.VNPAY_HASH_SECRET,
              config.VNPAY_PAYMENT_URL, config.VNPAY_RETURN_URL)
status = {
    'success': ('00', '00'),
    'cancel': ('24', '02'),
    'review': ('07', '07'),
    'pending': ('01', '01'),
}[args.status]
params = {
    'vnp_TmnCode': config.VNPAY_TMN_CODE,
    'vnp_TxnRef': args.order_id,
    'vnp_Amount': '5000000',  # 50.000 VND * 100
    'vnp_ResponseCode': status[0],
    'vnp_TransactionStatus': status[1],
    'vnp_TransactionNo': '999999999',
    'vnp_BankCode': 'NCB',
}
params['vnp_SecureHash'] = vnpay.sign_params(params)
url = 'http://127.0.0.1:8000/api/payment/ipn?' + urlencode(params)
with urlopen(url, timeout=5) as res:
    print('Phản hồi IPN MÔ PHỎNG:', res.read().decode('utf-8'))
with urlopen('http://127.0.0.1:8000/api/orders/' + args.order_id, timeout=5) as res:
    print('Trạng thái đơn hàng SQLite:', res.read().decode('utf-8'))
print('CHÚ Ý: Đây chỉ là IPN nội bộ tự ký, KHÔNG chứng minh VNPAY đã thanh toán.')
