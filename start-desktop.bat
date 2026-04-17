@echo off
echo ========================================
echo   Crazy Lister v3.0 - Desktop App
echo ========================================
echo.

:: Kill lingering processes
echo [1/2] Cleaning up old processes...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM pythonw.exe >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1
timeout /t 2 >nul

:: Launch PyWebView
echo [2/2] Launching Desktop App...
cd /d %~dp0backend
set PYTHONPATH=%CD%
start "" pythonw -m app.launcher

echo.
echo Application started in Desktop Mode!
echo You can close this terminal.
exit
