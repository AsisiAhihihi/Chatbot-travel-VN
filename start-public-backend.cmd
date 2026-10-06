@echo off
cd /d "%~dp0"
set FRONTEND_ORIGINS=https://asisiahihihi.github.io,http://127.0.0.1:5173,http://localhost:5173
set PUBLIC_DEPLOY=true
set CHAT_MAX_CONCURRENT=1
set CHAT_REQUESTS_PER_MINUTE=10
set PYTHONIOENCODING=utf-8
".venv\Scripts\python.exe" scripts\serve.py
pause