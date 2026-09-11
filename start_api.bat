@echo off
echo ============================================================
echo Starting CustomerPulse AI API Server
echo ============================================================
echo.
cd /d "%~dp0"
call venv\Scripts\activate
python app\main.py
pause
