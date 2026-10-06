@echo off
cd /d "%~dp0"
if exist "tools\cloudflared.exe" (
  "tools\cloudflared.exe" tunnel --url http://127.0.0.1:8000
) else (
  where cloudflared >nul 2>&1
  if errorlevel 1 (
    echo Install cloudflared first. See PUBLIC_WEB.md.
  ) else (
    cloudflared tunnel --url http://127.0.0.1:8000
  )
)
pause