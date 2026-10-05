@echo off
cd /d "%~dp0"
title Production Design Queue Manager - Design Queues watcher
echo ========================================
echo   Production Design Queue Manager
echo   Design Queues watcher
echo ========================================
echo.
python scripts\design_queues_watcher.py %*
