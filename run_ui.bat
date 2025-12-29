@echo off
setlocal
set SCRIPT_DIR=%~dp0
if exist "%SCRIPT_DIR%.venv\Scripts\python.exe" (
    "%SCRIPT_DIR%.venv\Scripts\python.exe" -m ui.settings_ui
) else (
    echo ".venv" не найден. Запусти 00_setup_repo.ps1 для подготовки окружения.
    python -m ui.settings_ui
)
if errorlevel 1 (
    echo UI exited with error %errorlevel%
    pause
)
