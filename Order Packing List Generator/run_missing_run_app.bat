@echo off
setlocal
cd /d "%~dp0"

echo ========================================
echo  Missing Run App - Setup and Launch
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
echo Starting Missing Run App...
start "" /D "%~dp0" pythonw missing_run_app.py
exit /b 0
