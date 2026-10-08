@echo off
REM Sets PY for the caller. No setlocal: the variable must survive the call.
set "PY="

where py >nul 2>&1
if not errorlevel 1 (
  py -c "import sys" >nul 2>&1
  if not errorlevel 1 set "PY=py"
)

if not defined PY (
  where python >nul 2>&1
  if not errorlevel 1 (
    python -c "import sys" >nul 2>&1
    if not errorlevel 1 set "PY=python"
  )
)

if not defined PY (
  echo.
  echo Python was not found.
  echo Install Python 3.12+ from https://www.python.org/downloads/
  echo During setup, check "Add python.exe to PATH".
  echo.
  exit /b 1
)

exit /b 0
