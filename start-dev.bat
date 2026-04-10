@echo off
echo ========================================
echo   Crazy Lister v3.0 - Development Start
echo ========================================
echo.

echo [1/3] Killing old processes...
taskkill /F /IM node.exe >nul 2>&1
taskkill /F /IM python.exe >nul 2>&1
timeout /t 2 >nul

echo [2/3] Starting Backend (Port 8765)...
start "CrazyLister Backend" cmd /k "cd backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8765 --log-level info"
timeout /t 3 >nul

echo [3/3] Starting Frontend (Port 3000)...
start "CrazyLister Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================
echo   Servers Started Successfully!
echo   Backend:  http://127.0.0.1:8765
echo   Frontend: http://localhost:3000
echo ========================================
echo.
echo Press any key to exit this window...
pause >nul
