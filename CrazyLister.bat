@echo off
:: If this opens a console, close it and relaunch silently via VBS
if "%1"=="SILENT" goto :run
start "" wscript.exe "%~dp0CrazyLister.vbs"
exit /b

:run
cd /d "%~dp0backend"
pythonw -m app.launcher
