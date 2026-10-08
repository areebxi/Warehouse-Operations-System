@echo off
setlocal EnableExtensions
cd /d "%~dp0\.."

call "%~dp0resolve_python.bat"
if errorlevel 1 (
  pause
  exit /b 1
)

%PY% -m scripts.app.main convert %*
if errorlevel 1 (
  set rc=%errorlevel%
  echo.
  pause
  exit /b %rc%
)

%PY% -m scripts.app.main print %*
set rc=%errorlevel%
echo.
pause
exit /b %rc%
