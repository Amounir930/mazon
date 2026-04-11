@echo off
setlocal enabledelayedexpansion

echo ========================================
echo   Crazy Lister v3.0 - Development Start
echo ========================================
echo.

:: Kill existing processes by window title
echo [1/4] Cleaning up old processes...
taskkill /F /FI "WINDOWTITLE eq Amazon Mock API*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq CrazyLister Backend*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq CrazyLister Frontend*" >nul 2>&1
timeout /t 2 >nul

:: Check if port 8765 is still in use
netstat -ano | findstr ":8765" | findstr "LISTENING" >nul 2>&1
if !errorlevel! equ 0 (
    echo    Port 8765 still in use, killing process...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8765" ^| findstr "LISTENING"') do taskkill /F /PID %%a >nul 2>&1
    timeout /t 2 >nul
)

:: Start Mock API (Port 9500)
echo [2/4] Starting Amazon Mock API (Port 9500)...
start "Amazon Mock API" cmd /k "cd /d %~dp0amazon-mock-api && node server.js"
timeout /t 3 >nul

:: Start Backend (Port 8765)
echo [3/4] Starting Backend (Port 8765)...
start "CrazyLister Backend" cmd /k "cd /d %~dp0backend && set PYTHONUNBUFFERED=1 && python -m uvicorn app.main:app --host 127.0.0.1 --port 8765 --log-level info --reload"
timeout /t 5 >nul

:: Start Frontend (Port 3000)
echo [4/4] Starting Frontend (Port 3000)...
start "CrazyLister Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ========================================
echo   All Servers Started Successfully!
echo   Mock API:  http://localhost:9500
echo   Backend:   http://127.0.0.1:8765
echo   Frontend:  http://localhost:3000
echo ========================================
echo.
echo Press any key to exit this window (Servers will keep running)...
pause >nul
