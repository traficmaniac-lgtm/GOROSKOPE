@echo off
:menu
cls
echo ============================
echo   GOROSKOPE Launcher
set SCRIPT_DIR=%~dp0
echo ============================
echo 1 ^) Setup (.venv + requirements)
echo 2 ^) Run UI
echo 3 ^) Run Bot
echo 4 ^) Git Pull
echo 5 ^) Exit
set /p choice=Select option:
if "%choice%"=="1" goto setup
if "%choice%"=="2" goto run_ui
if "%choice%"=="3" goto run_bot
if "%choice%"=="4" goto pull
if "%choice%"=="5" goto end
goto menu

:setup
echo Creating venv (if missing) and installing requirements...
if not exist "%SCRIPT_DIR%\.venv" (
    python -m venv "%SCRIPT_DIR%\.venv"
)
"%SCRIPT_DIR%\.venv\Scripts\python.exe" -m pip install --upgrade pip
"%SCRIPT_DIR%\.venv\Scripts\python.exe" -m pip install -r "%SCRIPT_DIR%requirements.txt"
pause
goto menu

:run_ui
call "%SCRIPT_DIR%run_ui.bat"
goto menu

:run_bot
call "%SCRIPT_DIR%run_bot.bat"
goto menu

:pull
call "%SCRIPT_DIR%pull.bat"
pause
goto menu

:end
exit /b
