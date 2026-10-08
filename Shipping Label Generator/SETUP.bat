@echo off
setlocal EnableExtensions

cd /d "%~dp0"

echo.
echo ============================================================
echo Shipping Label App - First-time Setup
echo ============================================================
echo.

call "%~dp0bat_files\resolve_python.bat"
if errorlevel 1 (
  pause
  exit /b 1
)

echo Python detected:
%PY% --version
echo.

echo Upgrading pip...
%PY% -m pip install --upgrade pip
if errorlevel 1 (
  echo.
  echo ERROR: Failed to upgrade pip.
  echo.
  pause
  exit /b 1
)

echo.
echo Installing dependencies from requirements.txt...
%PY% -m pip install -r requirements.txt
if errorlevel 1 (
  echo.
  echo ERROR: Dependency installation failed.
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
