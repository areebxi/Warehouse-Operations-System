@echo off
setlocal
cd /d "%~dp0"
title Export Custom Label Database (NocoDB)

echo ========================================
echo   Export Custom Label Database
echo   NocoDB / Postgres -^> live CSV
echo ========================================
echo.

python scripts\cl_db_exporter.py
set EXITCODE=%ERRORLEVEL%

echo.
if %EXITCODE% NEQ 0 (
    echo FAILED — export did not complete.
) else (
    echo Done.
)
pause
exit /b %EXITCODE%
