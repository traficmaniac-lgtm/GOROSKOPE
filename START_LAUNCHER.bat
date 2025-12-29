@echo off
setlocal enableextensions

echo === GOROSKOPE Launcher ===
where py >NUL 2>&1
if errorlevel 1 (
  echo Python Launcher "py" не найден. Установите Python 3.12 с поддержкой py -3.12.
  pause
  goto :eof
)

py -3.12 -V >NUL 2>&1
if errorlevel 1 (
  echo Требуется Python 3.12 (команда py -3.12). Установите/обновите Python.
  pause
  goto :eof
)

set PYTHON_CMD=py -3.12
set VENV_PY=.venv\Scripts\python.exe

if not exist .venv\Scripts\python.exe (
  echo Создаю виртуальное окружение .venv ...
  %PYTHON_CMD% -m venv .venv || (
    echo Не удалось создать виртуальное окружение.
    pause
    goto :eof
  )
)

echo Обновляю pip и зависимости...
%VENV_PY% -m pip install --upgrade pip
%VENV_PY% -m pip install -r requirements.txt || (
  echo Ошибка установки зависимостей. Проверьте интернет/права.
  pause
  goto :eof
)

echo Запускаю GUI...
%VENV_PY% launch.py

endlocal
