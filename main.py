from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from vnpay import VNPay

# Import thông tin cấu hình từ config.py
import config

app = FastAPI(title="VNPAY Sandbox Seminar Demo")

vnpay_service = VNPay(
    tmn_code=config.VNPAY_TMN_CODE,
    hash_secret=config.VNPAY_HASH_SECRET,
    payment_url=config.VNPAY_PAYMENT_URL,
    return_url=config.VNPAY_RETURN_URL
)

class PaymentPayload(BaseModel):
    order_id: str
    amount: int
    order_desc: str
    bank_code: str = ""

@app.get("/")
async def home():
    return FileResponse("templates/index.html")

@app.get("/payment/result")
async def payment_result():
    return FileResponse("templates/result.html")

@app.post("/api/payment/create-url")
async def create_payment_url(payload: PaymentPayload, request: Request):
    # Kiểm tra xem bạn sinh viên đã thay cấu hình chưa
    if "DIEN_MA" in config.VNPAY_TMN_CODE:
        return JSONResponse(
            status_code=400,
            content={"detail": "Bạn chưa cấu hình VNPAY_TMN_CODE trong file config.py!"}
        )

    client_ip = request.client.host if request.client else "127.0.0.1"
    now_str = datetime.now().strftime("%Y%m%d%H%M%S")

    params = {
        "vnp_Version": "2.1.0",
        "vnp_Command": "pay",
        "vnp_TmnCode": config.VNPAY_TMN_CODE,
        "vnp_Amount": str(payload.amount * 100),
        "vnp_CurrCode": "VND",
        "vnp_TxnRef": payload.order_id,
        "vnp_OrderInfo": payload.order_desc,
        "vnp_OrderType": "other",
        "vnp_Locale": "vn",
        "vnp_ReturnUrl": config.VNPAY_RETURN_URL,
        "vnp_IpAddr": client_ip,
        "vnp_CreateDate": now_str,
    }

    if payload.bank_code:
        params["vnp_BankCode"] = payload.bank_code

    url = vnpay_service.build_payment_url(params)
    return {"payment_url": url}

@app.get("/api/payment/verify")
async def verify_transaction(request: Request):
    query_params = dict(request.query_params)
    is_valid = vnpay_service.validate_response(query_params)
    return {
        "is_valid": is_valid,
        "response_code": query_params.get("vnp_ResponseCode"),
        "txn_ref": query_params.get("vnp_TxnRef"),
    }