@echo off
setlocal EnableExtensions

cd /d "%~dp0"

echo.
echo ============================================================
echo Shipping Label App - First-time Setup
echo ============================================================
echo.

REM 1) Verify Python launcher exists
py --version >nul 2>&1
if errorlevel 1 (
  echo ERROR: Python is not installed ^(or the 'py' launcher is missing^).
  echo.
  echo Fix:
  echo   - Install Python 3.12+ from https://www.python.org/downloads/
  echo   - During install, check "Add Python to PATH"
  echo   - Then re-run SETUP.bat
  echo.
  pause
  exit /b 1
)

echo Python detected:
py --version
echo.

REM 2) Upgrade pip tooling
echo Upgrading pip...
py -m pip install --upgrade pip
if errorlevel 1 (
  echo.
  echo ERROR: Failed to upgrade pip.
  echo.
  echo Troubleshooting:
  echo   - Right-click SETUP.bat and choose "Run as administrator"
  echo   - Ensure you have internet access and your firewall/proxy allows Python/pip
  echo   - Try running: py -m pip --version
  echo.
  pause
  exit /b 1
)

echo.
echo Installing dependencies from requirements.txt...
py -m pip install -r requirements.txt
if errorlevel 1 (
  echo.
  echo ERROR: Dependency installation failed.
  echo.
  echo Troubleshooting checklist:
  echo   - Right-click SETUP.bat and choose "Run as administrator"
  echo   - Verify Python/pip work:
  echo       py --version
  echo       py -m pip --version
  echo   - If you are behind a proxy/firewall, pip may be blocked.
  echo   - If permissions fail, use a virtual environment:
  echo       py -m venv .venv
  echo       .venv\\Scripts\\activate
  echo       py -m pip install -r requirements.txt
  echo.
  pause
  exit /b 1
)

echo.
echo Setup complete.
echo You can now double-click RUN.bat to start the app.
echo.
pause
exit /b 0

