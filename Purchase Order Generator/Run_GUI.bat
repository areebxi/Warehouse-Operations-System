@echo off
setlocal
cd /d "%~dp0"

echo ========================================
echo   ShipStation GUI - setup and run
echo ========================================
echo.

set "VENV=%~dp0.venv"
set "PY="

where python >nul 2>&1
if %errorlevel% equ 0 set "PY=python"

if not defined PY (
  where py >nul 2>&1
  if %errorlevel% equ 0 set "PY=py -3"
)

if not defined PY (
  echo [ERROR] Python not found.
  echo Install Python 3 from https://www.python.org/downloads/
  echo During setup, enable "Add python.exe to PATH".
  echo.
  pause
  exit /b 1
)

set "VENV_PY=%VENV%\Scripts\python.exe"

if exist "%VENV_PY%" (
  "%VENV_PY%" -c "import sys" >nul 2>&1
  if errorlevel 1 set "VENV_PY="
)

if not exist "%VENV_PY%" (
  if exist "%VENV%" (
    echo [1/3] Removing broken virtual environment...
    rmdir /s /q "%VENV%"
  )
  echo [1/3] Creating virtual environment...
  %PY% -m venv "%VENV%"
  if errorlevel 1 (
    echo [ERROR] Could not create .venv
    pause
    exit /b 1
  )
  set "VENV_PY=%VENV%\Scripts\python.exe"
)

echo [2/3] Upgrading pip and installing packages...
"%VENV_PY%" -m pip install --upgrade pip
if errorlevel 1 (
  echo [ERROR] pip upgrade failed
  pause
  exit /b 1
)

if not exist "requirements.txt" (
  echo [ERROR] requirements.txt missing in this folder.
  pause
  exit /b 1
)

"%VENV_PY%" -m pip install -r requirements.txt
if errorlevel 1 (
  echo [ERROR] pip install failed
  pause
  exit /b 1
)

echo [3/3] Starting GUI...
echo.
"%VENV_PY%" scripts\run_script_gui.py
if errorlevel 1 (
  echo.
  echo [ERROR] Script exited with an error.
  pause
  exit /b 1
)

endlocal
exit /b 0
