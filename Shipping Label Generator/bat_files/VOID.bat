@echo off
setlocal EnableExtensions

cd /d "%~dp0.."

py --version >nul 2>&1
if errorlevel 1 (
  echo Python is not installed ^(or the 'py' launcher is missing^).
  pause
  exit /b 1
)

py -c "import scripts" >nul 2>&1
if errorlevel 1 (
  echo Installing dependencies...
  py -m pip install -r requirements.txt
  if errorlevel 1 (
    echo Dependency install failed.
    pause
    exit /b 1
  )
)

REM Void ONE active shipment per order
py -m scripts.app.launchers.void_labels %*
set rc=%errorlevel%
echo.
pause
exit /b %rc%

