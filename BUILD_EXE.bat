@echo off
setlocal
title Crazy Lister v3.0 - Build System

echo ============================================================
echo   Crazy Lister v3.0 — Automatic EXE Builder
echo ============================================================
echo.

:: Check for PowerShell
where powershell >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] PowerShell is not found in your system.
    pause
    exit /b 1
)

:: Run the build script
echo [1/2] Starting the build process...
echo This may take a few minutes. Please wait.
echo.

powershell -ExecutionPolicy Bypass -File "%~dp0backend\build_release.ps1"

if %errorlevel% neq 0 (
    echo.
    echo ============================================================
    echo   [ERROR] BUILD FAILED!
    echo ============================================================
    echo Please check the error messages above.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   [SUCCESS] BUILD COMPLETED SUCCESSFULLY!
echo ============================================================
echo The release files are ready in: 
echo %~dp0releases\CrazyLister-v3.0.0\
echo.
echo Press any key to open the release folder and exit.
pause >nul
explorer "%~dp0releases\CrazyLister-v3.0.0\"
exit
