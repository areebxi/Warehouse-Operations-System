@echo off
setlocal
cd /d "%~dp0\.."
python scripts\sync_shipstation_tags.py %*
if errorlevel 1 pause
endlocal
