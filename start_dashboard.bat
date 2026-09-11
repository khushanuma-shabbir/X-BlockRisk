@echo off
echo ============================================================
echo Starting CustomerPulse AI Dashboard
echo ============================================================
echo.
cd /d "%~dp0"
call venv\Scripts\activate
streamlit run dashboard.py
pause
