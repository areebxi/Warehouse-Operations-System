@echo off
setlocal
cd /d "%~dp0"
title Order Packing List Generator

echo ========================================
echo   Order Packing List Generator
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
echo Starting Order Packing List Generator...
start "" /D "%~dp0" pythonw packing_list_app.py
exit /b 0
