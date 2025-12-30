@echo off
setlocal EnableExtensions

set LOG=logs\setup.log
if not exist logs mkdir logs

echo ===== GOROSKOPE START_ALL ===== > %LOG%
echo [%date% %time%] Старт установки >> %LOG%

where py >> %LOG% 2>>&1
if errorlevel 1 (
  echo Python Launcher "py" не найден. Установите Python 3.12 (py -3.12). >> %LOG%
  echo Python Launcher "py" не найден. Установите Python 3.12 (py -3.12).
  pause
  goto :eof
)

py -3.14 -V >NUL 2>&1
if not errorlevel 1 (
  echo Обнаружен Python 3.14. Этот проект поддерживает только Python 3.12. >> %LOG%
  echo Обнаружен Python 3.14. Этот проект поддерживает только Python 3.12.
  pause
  goto :eof
)

py -3.12 -V >> %LOG% 2>>&1
if errorlevel 1 (
  echo Требуется Python 3.12 (команда py -3.12). >> %LOG%
  echo Требуется Python 3.12 (команда py -3.12).
  pause
  goto :eof
)

echo Проверяю/создаю виртуальное окружение... >> %LOG%
set PYTHON_CMD=py -3.12
set VENV_PY=.venv\Scripts\python.exe

if not exist .venv\Scripts\python.exe (
  echo Создаю .venv >> %LOG%
  %PYTHON_CMD% -m venv .venv >> %LOG% 2>>&1 || (
    echo Не удалось создать виртуальное окружение. >> %LOG%
    echo Не удалось создать виртуальное окружение.
    pause
    goto :eof
  )
)

echo Обновляю pip и зависимости... >> %LOG%
%VENV_PY% -m pip install --upgrade pip >> %LOG% 2>>&1
%VENV_PY% -m pip install -r requirements.txt >> %LOG% 2>>&1
if errorlevel 1 (
  echo Ошибка установки зависимостей. См. %LOG% >> %LOG%
  echo Ошибка установки зависимостей. См. %LOG%
  pause
  goto :eof
)

if not exist .env (
  if exist .env.example (
    copy .env.example .env >> %LOG% 2>>&1
    echo Создан .env из .env.example >> %LOG%
  ) else (
    type nul > .env
    echo Создан пустой .env >> %LOG%
  )
  echo Откройте .env и вставьте BOT_TOKEN. >> %LOG%
  start notepad .env
)

echo Запускаю GUI Launcher... >> %LOG%
%VENV_PY% launch.py >> %LOG% 2>>&1
if errorlevel 1 (
  echo GUI завершился ошибкой. Смотрите %LOG%
) else (
  echo GUI запущен. >> %LOG%
)

echo Готово. Полный лог: %LOG%
endlocal
