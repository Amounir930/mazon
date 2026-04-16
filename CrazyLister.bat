@echo off
title Crazy Lister v3.0
color 0A

echo.
echo  ============================================
echo    Crazy Lister v3.0 - Amazon Listing Tool
echo  ============================================
echo.

:: Move to the project directory (same folder as this .bat file)
cd /d "%~dp0"

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

:: Check backend directory
if not exist "backend" (
    echo [ERROR] backend folder not found!
    echo Make sure this file is in the same folder as the project.
    pause
    exit /b 1
)

echo [OK] Starting Crazy Lister...
echo [OK] Logs saved to: %APPDATA%\CrazyLister\crazy_lister.log
echo.
echo  You can close this window after the app opens.
echo  ============================================
echo.

cd backend
python -m app.launcher

if errorlevel 1 (
    echo.
    echo [ERROR] App crashed! Check logs at: %APPDATA%\CrazyLister\crazy_lister.log
    pause
)
