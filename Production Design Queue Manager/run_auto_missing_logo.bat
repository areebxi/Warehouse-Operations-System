@echo off
cd /d "%~dp0"
title Production Design Queue Manager - Missing Logo watcher
echo ========================================
echo   Production Design Queue Manager
echo   Missing Logo watcher
echo ========================================
echo.
python scripts\auto_missing_logo_watcher.py %*
