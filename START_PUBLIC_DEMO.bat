@echo off
REM Public HTTPS demo: expose FastAPI through ngrok intentionally.
set "VNPAY_ENABLE_NGROK=1"
call "%~dp0START_DEMO.bat"
