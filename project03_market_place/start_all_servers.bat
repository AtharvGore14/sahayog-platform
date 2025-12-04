@echo off
echo Starting Sahayog Marketplace Servers...
echo.

REM Activate virtual environment
call venv\Scripts\activate

echo Starting Redis Server...
start "Redis Server" redis-server

echo Waiting for Redis to start...
timeout /t 3 /nobreak > nul

echo Starting Django Server (Daphne)...
start "Django Server" daphne -p 8000 sahayog_marketplace.asgi:application

echo Starting Celery Worker...
start "Celery Worker" celery -A sahayog_marketplace worker -l info --pool=solo

echo Starting Celery Beat Scheduler...
start "Celery Beat" celery -A sahayog_marketplace beat -l info

echo.
echo All servers started! Check the opened windows for any errors.
echo.
echo Django Server: http://127.0.0.1:8000
echo.
pause
