"""Cấu hình Sandbox. Không đưa Hash Secret thật lên GitHub."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / '.env')

VNPAY_TMN_CODE = os.getenv('VNPAY_TMN_CODE', '').strip()
VNPAY_HASH_SECRET = os.getenv('VNPAY_HASH_SECRET', '').strip()
VNPAY_PAYMENT_URL = 'https://sandbox.vnpayment.vn/paymentv2/vpcpay.html'
VNPAY_RETURN_URL = os.getenv('VNPAY_RETURN_URL', 'http://127.0.0.1:8000/payment/result').strip()
