@echo off
setlocal EnableExtensions
cd /d "%~dp0\.."

echo.
echo Label source report (app vs ShipStation-direct)
echo.

if not "%~1"=="" (
  py -m scripts.app.main label-report %*
  set rc=%errorlevel%
  goto finish
)

set /p REPORT_DATE="Enter date YYYY-MM-DD (press Enter for today): "
if "%REPORT_DATE%"=="" (
  py -m scripts.app.main label-report
) else (
  py -m scripts.app.main label-report --date %REPORT_DATE%
)
set rc=%errorlevel%

:finish
echo.
echo Each run saves a new timestamped file under Reports\^<date^>\
echo.
pause
exit /b %rc%
