@echo off
setlocal
cd /d "%~dp0"
title Order Packing List Generator - Missing Run

echo ========================================
echo   Order Packing List Generator
echo   Missing Run
echo ========================================
echo.

echo Installing dependencies...
python -m pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo Starting Missing Run...
start "" /D "%~dp0" pythonw missing_run_app.py
exit /b 0
