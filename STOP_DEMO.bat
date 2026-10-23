@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"
title VNPAY - Stop Demo

echo ================================================
echo     VNPAY - STOP ONE CLICK DEMO (WINDOWS)
echo ================================================

if not exist "%~dp0stop_demo_windows.ps1" (
  echo [ERROR] Missing stop_demo_windows.ps1 in the project folder.
  pause
  exit /b 1
)

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0stop_demo_windows.ps1"
set "RESULT=%ERRORLEVEL%"
echo.
if "%RESULT%"=="0" (
  echo [DONE] Stop operation finished.
) else (
  echo [WARN] Could not stop one or more demo processes. Read the messages above.
)
echo You may close this window.
pause
exit /b %RESULT%
