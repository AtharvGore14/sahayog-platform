@echo off
echo ========================================
echo FORCE RESET DATABASE
echo ========================================
echo.
echo Stopping all Python processes...
taskkill /F /IM python.exe 2>nul
if %errorlevel% equ 0 (
    echo Python processes stopped.
) else (
    echo No Python processes found or already stopped.
)

timeout /t 2 /nobreak >nul

echo.
echo Deleting database file...
if exist waste_ledger.db (
    del /F waste_ledger.db
    echo Database deleted.
) else (
    echo Database file not found.
)

echo.
echo Resetting database schema...
py backend\reset_db.py

echo.
echo Seeding database with sample data...
py setup.py

echo.
echo ========================================
echo Database reset complete!
echo ========================================
echo.
echo You can now start the server with: py run_server.py
pause

