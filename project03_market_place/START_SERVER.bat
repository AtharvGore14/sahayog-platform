@echo off
echo ========================================
echo   SAHAYOG AI MARKETPLACE SERVER
echo ========================================
echo.

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Starting Django server...
echo Marketplace will be available at: http://127.0.0.1:8000
echo.

python manage.py runserver 127.0.0.1:8000

pause
