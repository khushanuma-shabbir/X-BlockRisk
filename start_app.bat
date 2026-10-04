@echo off
echo ========================================
echo  Blockchain Fraud Detection System
echo  Starting Production Server...
echo ========================================
echo.

REM Check if Redis is running (optional but recommended)
echo [1/3] Checking Redis connection...
redis-cli ping >nul 2>&1
if %errorlevel% == 0 (
    echo ✓ Redis is running
) else (
    echo ⚠ Redis not detected - Cache layer disabled
    echo   To enable caching: Install and start Redis
)

echo.
echo [2/3] Validating Python environment...
python -c "import streamlit, torch, pandas" 2>nul
if %errorlevel% == 0 (
    echo ✓ All dependencies installed
) else (
    echo ✗ Missing dependencies
    echo   Run: pip install -r requirements.txt
    pause
    exit /b 1
)

echo.
echo [3/3] Starting Streamlit server...
echo.
echo ========================================
echo  Server will start at:
echo  http://localhost:8501
echo ========================================
echo.
echo Press Ctrl+C to stop the server
echo.

streamlit run src/app.py

pause
