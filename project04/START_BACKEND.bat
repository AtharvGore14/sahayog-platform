@echo off
echo ========================================
echo Starting Automated Waste Financial Ledger Backend
echo ========================================
echo.
echo Checking Python installation...
python --version
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

echo.
echo Checking dependencies...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
)

echo.
echo Starting backend server...
echo Server will be available at: http://localhost:8000
echo API docs will be available at: http://localhost:8000/docs
echo.
echo Press CTRL+C to stop the server
echo ========================================
echo.

py run_server.py

pause

