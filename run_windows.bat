@echo off
cd /d "%~dp0"
if not exist .venv python -m venv .venv
call .venv\Scripts\activate
python -m pip install -r backend\requirements.txt
if not exist .env copy .env.example .env
echo.
echo Put your Sarvam API key in .env, then press any key to start.
pause >nul
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
