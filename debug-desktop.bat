@echo off
echo ========================================
echo   Crazy Lister v3.0 - DEBUG MODE
echo ========================================
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found in PATH. Please install Python.
    pause
    exit /b
)

:: Kill lingering processes
echo [1/3] Cleaning up old processes...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM pythonw.exe >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1
timeout /t 1 >nul

:: Install dependencies if missing (optional, but good for debug)
echo [2/3] Checking dependencies...
cd /d %~dp0backend
pip install -r requirements.txt

:: Launch with console visible
echo [3/3] Launching Desktop App (Console Visible)...
set PYTHONPATH=%CD%
python -m app.launcher

echo.
if %errorlevel% neq 0 (
    echo [ERROR] Application crashed with exit code %errorlevel%
)
pause
