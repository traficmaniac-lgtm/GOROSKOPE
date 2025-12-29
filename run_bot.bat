@echo off
setlocal
set SCRIPT_DIR=%~dp0
if exist "%SCRIPT_DIR%.venv\Scripts\python.exe" (
    "%SCRIPT_DIR%.venv\Scripts\python.exe" -m app.bot
) else (
    python -m app.bot
)
if errorlevel 1 (
    echo Bot exited with error %errorlevel%
    pause
)
