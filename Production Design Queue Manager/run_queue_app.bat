@echo off
chcp 65001 >nul
title Queue App - Canvas Layout Tool
color 0A

echo ========================================
echo   Queue App - Canvas Layout Tool
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH!
    echo.
    echo Please install Python from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo [✓] Python found
python --version
echo.

REM Get the directory where the batch file is located (project root)
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM Check if requirements.txt exists
if not exist "requirements.txt" (
    echo [WARNING] requirements.txt not found!
    echo Creating requirements.txt...
    (
        echo pandas^>=2.0.0
        echo openpyxl^>=3.1.0
        echo Pillow^>=10.0.0
    ) > requirements.txt
)

REM Check if Python script exists
if not exist "queue_app.py" (
    echo [ERROR] queue_app.py not found!
    echo Please make sure you're running this batch file from the project root directory.
    echo.
    pause
    exit /b 1
)

echo [INFO] Installing/Updating dependencies...
echo.

REM Install dependencies
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt --quiet

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to install dependencies!
    echo Please check your internet connection and try again.
    echo.
    pause
    exit /b 1
)

echo [✓] Dependencies installed successfully
echo.

REM Use pythonw so the GUI runs without a CMD window.
pythonw --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] pythonw is not available!
    echo The app needs pythonw to start without a console window.
    echo.
    pause
    exit /b 1
)

REM Start the app detached so this setup window can close immediately.
REM /MAX avoids Windows inheriting a minimized state from the closing console.
echo [INFO] Starting Queue App (no console window)...
echo.
start "" /MAX pythonw "%SCRIPT_DIR%queue_app.py"
if errorlevel 1 (
    echo.
    echo [ERROR] Failed to start the application!
    echo.
    pause
    exit /b 1
)

exit /b 0

