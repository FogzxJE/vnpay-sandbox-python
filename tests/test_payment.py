"""Mocked/signed callbacks: không kết nối VNPAY thật; chỉ chứng minh logic ứng dụng."""
import os
from pathlib import Path
from urllib.parse import parse_qs, urlparse

# Tự động test với credentials giả, không cần tài khoản Sandbox.
os.environ['VNPAY_TMN_CODE'] = 'TEST1234'
os.environ['VNPAY_HASH_SECRET'] = 'LOCAL_TEST_SECRET_NOT_FOR_LIVE_PAYMENT'

import pytest
from fastapi.testclient import TestClient
import main


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(main, 'DB_PATH', tmp_path / 'orders.db')
    with TestClient(main.app) as c:
        yield c


def order_from_url(client):
    response = client.post('/api/payment/create-url', json={'bank_code': 'NCB'})
    assert response.status_code == 200
    data = response.json()
    signed_params = parse_qs(urlparse(data['payment_url']).query)
    assert signed_params['vnp_Amount'][0] == '5000000'
    assert signed_params['vnp_TxnRef'][0] == data['order_id']
    return data['order_id']


def signed_response(order_id, *, amount='5000000', result='00', txn_status='00', merchant='TEST1234'):
    params = {
        'vnp_Amount': amount,
        'vnp_TmnCode': merchant,
        'vnp_TxnRef': order_id,
        'vnp_ResponseCode': result,
        'vnp_TransactionStatus': txn_status,
        'vnp_TransactionNo': '12345678',
        'vnp_BankCode': 'NCB',
    }
    params['vnp_SecureHash'] = main.vnpay_service.sign_params(params)
    return params


def test_home_and_docs(client):
    assert client.get('/').status_code == 200
    assert client.get('/payment/result').status_code == 200
    assert client.get('/docs').status_code == 200


def test_server_controls_amount_and_order_id(client):
    result = client.post('/api/payment/create-url', json={'bank_code': 'NCB', 'amount': -50000})
    assert result.status_code == 422  # Extra input bị từ chối.
    order_id = order_from_url(client)
    assert client.get('/api/orders/' + order_id).json()['amount_vnd'] == 50_000


def test_return_url_never_marks_paid(client):
    order_id = order_from_url(client)
    ret = client.get('/api/payment/verify', params=signed_response(order_id)).json()
    assert ret['is_valid'] is True
    assert ret['gateway_success'] is True
    assert ret['is_paid'] is False
    assert client.get('/api/orders/' + order_id).json()['status'] == 'PENDING'


def test_ipn_success_then_duplicate(client):
    order_id = order_from_url(client)
    params = signed_response(order_id)
    assert client.get('/api/payment/ipn', params=params).json()['RspCode'] == '00'
    assert client.get('/api/orders/' + order_id).json()['status'] == 'PAID'
    assert client.get('/api/payment/ipn', params=params).json()['RspCode'] == '02'
    assert client.get('/api/payment/verify', params=params).json()['is_paid'] is True


def test_ipn_invalid_signature(client):
    order_id = order_from_url(client)
    params = signed_response(order_id)
    params['vnp_Amount'] = '123'  # Sửa dữ liệu nhưng giữ nguyên chữ ký.
    assert client.get('/api/payment/ipn', params=params).json()['RspCode'] == '97'
    assert client.get('/api/orders/' + order_id).json()['status'] == 'PENDING'


def test_ipn_wrong_amount(client):
    order_id = order_from_url(client)
    assert client.get('/api/payment/ipn', params=signed_response(order_id, amount='100')).json()['RspCode'] == '04'
    assert client.get('/api/orders/' + order_id).json()['status'] == 'PENDING'


def test_ipn_unknown_order(client):
    assert client.get('/api/payment/ipn', params=signed_response('HD_UNKNOWN')).json()['RspCode'] == '01'


def test_ipn_wrong_merchant(client):
    order_id = order_from_url(client)
    assert client.get('/api/payment/ipn', params=signed_response(order_id, merchant='BADCODE1')).json()['RspCode'] == '99'


def test_ipn_failed_transaction(client):
    order_id = order_from_url(client)
    assert client.get('/api/payment/ipn', params=signed_response(order_id, result='24', txn_status='02')).json()['RspCode'] == '00'
    assert client.get('/api/orders/' + order_id).json()['status'] == 'FAILED'


def test_ipn_unfinished_transaction(client):
    order_id = order_from_url(client)
    assert client.get('/api/payment/ipn', params=signed_response(order_id, result='01', txn_status='01')).json()['RspCode'] == '99'
    assert client.get('/api/orders/' + order_id).json()['status'] == 'PENDING'


def test_ipn_duplicate_parameters(client):
    order_id = order_from_url(client)
    params = signed_response(order_id)
    from urllib.parse import urlencode
    query = urlencode(params) + '&vnp_TxnRef=OTHER'
    assert client.get('/api/payment/ipn?' + query).json()['RspCode'] == '99'
