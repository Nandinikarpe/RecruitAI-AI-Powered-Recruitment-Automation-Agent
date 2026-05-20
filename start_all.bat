@echo off
cd /d "%~dp0"
if exist venv\Scripts\activate.bat call venv\Scripts\activate.bat
echo Starting FastAPI on http://127.0.0.1:8001 ...
start "Recruitment API" cmd /k uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
timeout /t 3 /nobreak >nul
echo Starting Streamlit...
streamlit run streamlit_app.py
