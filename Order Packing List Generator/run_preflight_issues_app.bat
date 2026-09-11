@echo off
setlocal
cd /d "%~dp0"
title Order Packing List Generator - Preflight Issues

echo ========================================
echo   Order Packing List Generator
echo   Preflight Issues
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
echo Starting Preflight Issues...
start "" /D "%~dp0" pythonw preflight_issues_app.py
exit /b 0
