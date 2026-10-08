@echo off
setlocal EnableExtensions
cd /d "%~dp0\.."

call "%~dp0resolve_python.bat"
if errorlevel 1 (
  pause
  exit /b 1
)

echo.
echo Label source report (app vs ShipStation-direct)
echo.

if not "%~1"=="" (
  %PY% -m scripts.app.main label-report %*
  set rc=%errorlevel%
  goto finish
)

set /p REPORT_DATE="Enter date YYYY-MM-DD (press Enter for today): "
if "%REPORT_DATE%"=="" (
  %PY% -m scripts.app.main label-report
) else (
  %PY% -m scripts.app.main label-report --date %REPORT_DATE%
)
set rc=%errorlevel%

:finish
echo.
echo Each run saves a new timestamped file under Reports\^<date^>\
echo.
pause
exit /b %rc%
