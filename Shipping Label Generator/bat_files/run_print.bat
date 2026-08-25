@echo off
setlocal EnableExtensions
cd /d "%~dp0\.."

py -m scripts.app.main print %*
set rc=%errorlevel%
echo.
pause
exit /b %rc%
