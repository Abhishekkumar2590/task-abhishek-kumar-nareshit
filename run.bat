@echo off
REM Setup and run script for Flask-Celery-RabbitMQ project (Windows)

echo ================================
echo Flask-Celery-RabbitMQ Setup
echo ================================

REM Check if venv exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing dependencies...
pip install -r requirements.txt

echo.
echo ================================
echo Setup Complete!
echo ================================
echo.
echo Now start in separate terminals:
echo.
echo Terminal 1 (Flask):
echo   venv\Scripts\activate
echo   python app.py
echo.
echo Terminal 2 (Celery Worker):
echo   venv\Scripts\activate
echo   celery -A worker worker --loglevel=info
echo.
echo Terminal 3 (Test):
echo   venv\Scripts\activate
echo   python test_endpoints.py
echo.
pause
