@echo off
setlocal EnableExtensions

cd /d "%~dp0.."

call "%~dp0resolve_python.bat"
if errorlevel 1 (
  pause
  exit /b 1
)

%PY% -c "import scripts" >nul 2>&1
if errorlevel 1 (
  echo Installing dependencies...
  %PY% -m pip install -r requirements.txt
  if errorlevel 1 (
    echo Dependency install failed.
    pause
    exit /b 1
  )
)

REM Void ONE active shipment per order
%PY% -m scripts.app.launchers.void_labels %*
set rc=%errorlevel%
echo.
pause
exit /b %rc%
