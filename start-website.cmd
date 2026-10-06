@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
 echo Missing Python environment: .venv
 pause
 exit /b 1
)
if not exist "frontend\node_modules\.bin\vite.cmd" (
 echo Missing frontend dependencies. Run npm install in frontend first.
 pause
 exit /b 1
)
start "RAG Backend - keep open" /D "%~dp0" cmd /k ".venv\Scripts\python.exe scripts\serve.py"
start "Frontend - keep open" /D "%~dp0frontend" cmd /k "npm run dev -- --port 5173 --strictPort"
echo Waiting for the frontend...
powershell -NoProfile -Command "$ready=$false; for($i=0;$i -lt 30;$i++){try{$r=Invoke-WebRequest -UseBasicParsing 'http://127.0.0.1:5173/' -TimeoutSec 2; if($r.StatusCode -eq 200){$ready=$true;break}}catch{}; Start-Sleep -Seconds 1}; if($ready){Start-Process 'http://127.0.0.1:5173/'; Write-Host 'Frontend is ready. Keep both server windows open.'}else{Write-Host 'Frontend did not start. Check the Frontend window for errors.'; exit 1}"
if errorlevel 1 pause
endlocal