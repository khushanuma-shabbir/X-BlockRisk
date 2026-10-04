@echo off
echo ========================================
echo  Restarting Fraud Detection System
echo ========================================
echo.

echo [1/2] Stopping existing Streamlit processes...
taskkill /F /IM streamlit.exe 2>nul
taskkill /F /IM python.exe /FI "WINDOWTITLE eq streamlit*" 2>nul
timeout /t 2 >nul

echo [2/2] Starting fresh instance...
echo.
echo ========================================
echo  Opening at: http://localhost:8501
echo ========================================
echo.

cd /d "%~dp0"
start /B streamlit run src/app.py --server.headless true

timeout /t 3 >nul
start http://localhost:8501

echo.
echo ✓ App started!
echo   If browser didn't open, go to: http://localhost:8501
echo.
pause
