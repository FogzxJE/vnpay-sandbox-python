@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0.."
title VNPAY - One Click Startup

echo ========================================================
echo  VNPAY SANDBOX SEMINAR - ONE CLICK START
 echo ========================================================

if not exist "main.py" (
  echo [ERROR] main.py not found. Put the launcher folder inside the project root.
  goto :fail
)

if not exist ".env" (
  if exist ".env.example" (
    copy /y ".env.example" ".env" >nul
    echo [INFO] Created .env from .env.example.
    echo [INFO] For REAL Sandbox checkout, edit .env with valid VNPAY credentials.
  )
)

REM A copied .venv can contain an invalid Python path from another computer.
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -c "import sys" >nul 2>nul
  if errorlevel 1 (
    echo [WARN] This Python environment is broken or copied from another computer.
    echo [INFO] Recreating .venv for this computer...
    rmdir /s /q ".venv"
    if exist ".venv" (
      echo [ERROR] Could not remove .venv. Close VS Code terminals using it and retry.
      goto :fail
    )
  )
)

if not exist ".venv\Scripts\python.exe" (
  echo [1/3] Creating Python virtual environment...
  where py >nul 2>nul
  if not errorlevel 1 (
    py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul
    if not errorlevel 1 (
      py -3 -m venv ".venv"
      if errorlevel 1 goto :fail
      goto :venv_ready
    )
  )
  where python >nul 2>nul
  if not errorlevel 1 (
    python -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul
    if not errorlevel 1 (
      python -m venv ".venv"
      if errorlevel 1 goto :fail
      goto :venv_ready
    )
  )
  echo [ERROR] Python 3.10+ is not installed or not available on PATH.
  echo Install Python from https://www.python.org/downloads/windows/
  goto :fail
)

:venv_ready
echo [2/3] Checking project dependencies...
".venv\Scripts\python.exe" -c "import fastapi,uvicorn,dotenv" >nul 2>nul
if errorlevel 1 (
  echo [INFO] Installing requirements for the first run. Internet is required.
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt
  if errorlevel 1 (
    echo [ERROR] Could not install required packages. Check Internet / firewall / pip log above.
    goto :fail
  )
)

echo [3/3] Starting application...
".venv\Scripts\python.exe" "one_click_launcher.py"
if errorlevel 1 goto :fail

echo [DONE] The application was launched. Keep the FastAPI/ngrok consoles open.
echo You may close this startup window.
exit /b 0

:fail
echo.
echo Startup failed. Fix the problem above and double-click START_DEMO.bat again.
pause
exit /b 1
