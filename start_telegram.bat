@echo off
echo ========================================
echo    ACUMEN - Telegram Bot
echo ========================================
echo.
echo Starting Acumen Telegram Bot...
echo Press Ctrl+C to stop
echo.
cd /d %USERPROFILE%\acumen
call .venv\Scripts\activate.bat
if errorlevel 1 (echo ERROR: Could not activate virtual environment & pause & exit)
python -m acumen.interface.telegram_bot
pause