@echo off
setlocal EnableExtensions

cd /d "%~dp0"

call "%~dp0bat_files\resolve_python.bat"
if errorlevel 1 (
  pause
  exit /b 1
)

REM Auto-dependency install: if imports fail, install requirements
%PY% -c "import scripts" >nul 2>&1
if errorlevel 1 (
  echo.
  echo Installing dependencies... this may take a minute.
  %PY% -m pip install -r requirements.txt
  if errorlevel 1 (
    echo.
    echo Dependency install failed.
    pause
    exit /b 1
  )
)

REM Start the real entrypoint (interactive menu)
%PY% -c "from scripts.app.util.win_console import configure_windows_console as c; c()"
%PY% -m scripts.app.launchers.shipping_system
set rc=%errorlevel%
echo.
pause
exit /b %rc%
