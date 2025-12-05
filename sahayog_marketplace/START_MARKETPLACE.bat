@echo off
echo ========================================
echo   SAHAYOG AI MARKETPLACE LAUNCHER
echo ========================================
echo.

echo Starting Django server...
cd /d "%~dp0"
call venv\Scripts\activate.bat
start "Django Server" python manage.py runserver 127.0.0.1:8000

echo.
echo Waiting for server to start...
timeout /t 3 /nobreak > nul

echo.
echo ========================================
echo   MARKETPLACE IS READY!
echo ========================================
echo.
echo Opening marketplace in browser...
start "" "LAUNCH_MARKETPLACE.html"

echo.
echo ========================================
echo   ACCESS YOUR MARKETPLACE:
echo ========================================
echo.
echo 🌐 Browser: http://127.0.0.1:8000
echo 🎨 Frontend: ai_enhanced_frontend.html
echo 🚀 Launcher: LAUNCH_MARKETPLACE.html
echo.
echo 🔑 Demo Accounts:
echo    admin / admin123
echo    DemoS (Seller) / demo123
echo    DemoB (Buyer) / demo123
echo    eco_seller / demo123
echo    green_recycler / demo123
echo.
echo Press any key to exit...
pause > nul
