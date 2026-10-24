"""Tạo URL và xác minh chữ ký VNPAY v2.1.0."""
import hashlib
import hmac
from urllib.parse import quote_plus


class VNPay:
    def __init__(self, tmn_code: str, hash_secret: str, payment_url: str, return_url: str):
        self.tmn_code = tmn_code
        self.hash_secret = hash_secret
        self.payment_url = payment_url
        self.return_url = return_url

    @staticmethod
    def canonical_query(params: dict) -> str:
        """Sắp xếp key A-Z, encode value theo application/x-www-form-urlencoded."""
        pairs = sorted(
            (k, str(v)) for k, v in params.items()
            if k.startswith('vnp_')
            and k not in ('vnp_SecureHash', 'vnp_SecureHashType')
            and v is not None and str(v) != ''
        )
        return '&'.join(f'{k}={quote_plus(v, safe="")}' for k, v in pairs)

    def sign_params(self, params: dict) -> str:
        content = self.canonical_query(params).encode('utf-8')
        return hmac.new(self.hash_secret.encode('utf-8'), content, hashlib.sha512).hexdigest()

    def build_payment_url(self, params: dict) -> str:
        if not self.tmn_code or not self.hash_secret:
            raise ValueError('Sandbox credentials are missing')
        query = self.canonical_query(params)
        signature = self.sign_params(params)
        return f'{self.payment_url}?{query}&vnp_SecureHash={signature}'

    def validate_response(self, params: dict) -> bool:
        incoming = params.get('vnp_SecureHash', '')
        if not self.hash_secret or len(incoming) != 128:
            return False
        try:
            bytes.fromhex(incoming)
        except ValueError:
            return False
        expected = self.sign_params(params)
        return hmac.compare_digest(incoming.lower(), expected.lower()) 
