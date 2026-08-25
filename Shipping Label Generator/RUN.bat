@echo off
setlocal EnableExtensions

cd /d "%~dp0"

REM 1) Environment check: verify Python is installed
py --version >nul 2>&1
if errorlevel 1 (
  echo.
  echo Python is not installed ^(or the 'py' launcher is missing^).
  echo Install Python 3.12+ from https://www.python.org/downloads/ and try again.
  echo.
  pause
  exit /b 1
)

REM 2) Auto-dependency install: if imports fail, install requirements
py -c "import scripts" >nul 2>&1
if errorlevel 1 (
  echo.
  echo Installing dependencies... this may take a minute.
  py -m pip install -r requirements.txt
  if errorlevel 1 (
    echo.
    echo Dependency install failed.
    pause
    exit /b 1
  )
)

REM 3) Start the real entrypoint (interactive menu)
py -c "from scripts.app.util.win_console import configure_windows_console as c; c()"
py -m scripts.app.launchers.shipping_system
set rc=%errorlevel%
echo.
pause
exit /b %rc%

