@echo off
echo ========================================
echo Resetting Database
echo ========================================
echo.
echo IMPORTANT: Make sure the server is stopped!
echo Press any key to continue or CTRL+C to cancel...
pause

echo.
echo Deleting old database...
if exist waste_ledger.db (
    del waste_ledger.db
    echo Database deleted.
) else (
    echo Database file not found (may already be deleted).
)

echo.
echo Creating new database with updated schema...
py setup.py

echo.
echo Done! You can now start the server with: py run_server.py
pause

