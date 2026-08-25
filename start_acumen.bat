@echo off
title Acumen Startup
echo.
echo  ============================================
echo    ACUMEN AI - SYSTEM STARTUP
echo  ============================================
echo.

echo  [1/3] Starting Rust DAG Scheduler on :9090...
start "Acumen Scheduler" /D "%USERPROFILE%\acumen\engine\scheduler" target\release\acumen-scheduler.exe
timeout /t 2 /nobreak >nul

echo  [2/3] Starting Go Worker Pool on :9091...
start "Acumen Workers" /D "%USERPROFILE%\acumen\engine\worker" bin\acumen-worker.exe
timeout /t 2 /nobreak >nul

echo  [3/3] Starting FastAPI on :8000...
start "Acumen API" powershell -NoExit -Command "cd $env:USERPROFILE\acumen; .\.venv\Scripts\Activate.ps1; python start_api.py"
timeout /t 8 /nobreak >nul

echo.
echo  ============================================
echo    ALL SERVICES LAUNCHED!
echo  ============================================
echo.
echo    Scheduler:  http://127.0.0.1:9090
echo    Workers:    http://127.0.0.1:9091
echo    Web UI:     http://127.0.0.1:8000
echo.

start http://127.0.0.1:8000

echo  Running KB Health Check...
cd /d %USERPROFILE%\acumen && .\.venv\Scripts\activate.bat && python kb_health.py

echo  Press any key to close this window...
pause >nul