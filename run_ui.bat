@echo off
setlocal
set SCRIPT_DIR=%~dp0
if exist "%SCRIPT_DIR%.venv\Scripts\python.exe" (
    "%SCRIPT_DIR%.venv\Scripts\python.exe" -m ui.settings_ui
) else (
    python -m ui.settings_ui
)
if errorlevel 1 (
    echo UI exited with error %errorlevel%
    pause
)
