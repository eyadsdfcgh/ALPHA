@echo off
setlocal
cd /d "%~dp0"

title Cloudflare Tunnel - Public Access

echo ========================================================
echo   Sharing VR Board with the World (Cloudflare Tunnel)
echo   مشاركة الموقع مع أي شخص خارج الشبكة
echo ========================================================
echo.

:: 1. Check if Server is likely running (simple check)
echo [NOTE] Make sure your local server is RUNNING (start_server.bat) before using this!
echo [تنبيه] تأكد أن سيرفر الموقع يعمل أولاً.
echo.

:: 2. Set Path to Cloudflared
set "CLOUDFLARED_PATH=C:\Program Files (x86)\cloudflared\cloudflared.exe"

if not exist "%CLOUDFLARED_PATH%" (
    echo [ERROR] Cloudflared not found at: "%CLOUDFLARED_PATH%"
    echo Please check the path or install it.
    pause
    exit /b
)

echo [OK] Found Cloudflared at: "%CLOUDFLARED_PATH%"
echo.
echo ========================================================
echo   Starting Tunnel...
echo   Wait for the link ending in .trycloudflare.com
echo   انتظر ظهور الرابط في الأسفل
echo ========================================================
echo.

:: 3. Run Tunnel
"%CLOUDFLARED_PATH%" tunnel --url http://localhost:5000

pause
