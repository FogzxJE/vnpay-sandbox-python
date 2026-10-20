import hashlib
import hmac
import urllib.parse


class VNPay:

  def __init__(
      self,
      tmn_code: str,
      hash_secret: str,
      payment_url: str,
      return_url: str,
  ):
    self.tmn_code = tmn_code
    self.hash_secret = hash_secret
    self.payment_url = payment_url
    self.return_url = return_url

  def build_payment_url(self, params: dict) -> str:
    # 1. Sắp xếp tham số A-Z và loại bỏ giá trị rỗng
    sorted_params = sorted([
        (k, v) for k, v in params.items() if v is not None and str(v) != ''
    ])

    # 2. Tạo chuỗi query string
    query_parts = [
        f'{k}={urllib.parse.quote_plus(str(v))}' for k, v in sorted_params
    ]
    query_string = '&'.join(query_parts)

    # 3. Tạo chữ ký băm HMAC-SHA512
    secure_hash = hmac.new(
        self.hash_secret.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha512,
    ).hexdigest()

    return f'{self.payment_url}?{query_string}&vnp_SecureHash={secure_hash}'

  def validate_response(self, response_params: dict) -> bool:
    received_hash = response_params.get('vnp_SecureHash', '')
    valid_params = {
        k: v
        for k, v in response_params.items()
        if k.startswith('vnp_') and k not in ['vnp_SecureHash', 'vnp_SecureHashType']
    }
    sorted_params = sorted(valid_params.items())
    query_string = '&'.join([
        f'{k}={urllib.parse.quote_plus(str(v))}'
        for k, v in sorted_params
        if v is not None and str(v) != ''
    ])

    calculated_hash = hmac.new(
        self.hash_secret.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha512,
    ).hexdigest()

    return received_hash.lower() == calculated_hash.lower()