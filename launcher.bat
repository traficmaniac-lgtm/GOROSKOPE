@echo off
:menu
cls
echo ============================
echo   GOROSKOPE Launcher
set SCRIPT_DIR=%~dp0
echo ============================
echo 1 ^) Run UI
echo 2 ^) Run Bot
echo 3 ^) Exit
set /p choice=Select option: 
if "%choice%"=="1" goto run_ui
if "%choice%"=="2" goto run_bot
if "%choice%"=="3" goto end
goto menu

:run_ui
call "%SCRIPT_DIR%run_ui.bat"
goto menu

:run_bot
call "%SCRIPT_DIR%run_bot.bat"
goto menu

:end
exit /b
