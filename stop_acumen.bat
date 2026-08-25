@echo off
title Acumen Shutdown
echo.
echo  ============================================
echo    ACUMEN AI - SHUTTING DOWN
echo  ============================================
echo.

echo  [1/3] Stopping FastAPI...
taskkill /IM python.exe /F >nul 2>&1
echo         Done.

echo  [2/3] Stopping Rust Scheduler...
taskkill /IM acumen-scheduler.exe /F >nul 2>&1
echo         Done.

echo  [3/3] Stopping Go Workers...
taskkill /IM acumen-worker.exe /F >nul 2>&1
echo         Done.

echo.
echo  ============================================
echo    ALL SERVICES STOPPED
echo  ============================================
echo.
echo  Press any key to close...
pause >nul
