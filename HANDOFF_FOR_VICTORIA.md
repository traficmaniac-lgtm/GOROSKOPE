1) Версия этапа: v0.3
2) Что было сломано/риски:
- GUI падал без .env/BOT_TOKEN и не показывал статус среды, логи писались в корень bot.log, не было запуска «в 2 клика».
- Бот стартовал без явных проверок токена, ошибки не доходили до пользователя/логов лаунчера.
3) Что исправлено:
- Добавлен защитный запуск GUI с логированием в logs/launcher.log, предложением создать .env из .env.example и статус-блоком (Python, интерпретатор, .venv, БД, логи).
- Вкладка «Настройки» реально сохраняет/проверяет .env, ошибки и результат выводятся через messagebox + лог; тест AI и пинг OpenAI показывают режим (stub/OpenAI) и логируют ошибки.
- Бот/CLI: строгая проверка BOT_TOKEN (StartupError), fallback на StubAI при проблемах с OpenAI SDK/ключом, глобальный error handler и логи в logs/app.log; BotRunner валидирует .env перед запуском и показывает ошибки в GUI.
- Добавлены скрипты START_LAUNCHER.bat (py -3.12, авто .venv, install, запуск GUI) и START_LAUNCHER_SILENT.vbs.
4) Как запускать:
- Windows: двойной клик по START_LAUNCHER.bat (требуется установленный Python Launcher py -3.12). После открытия GUI можно сохранить .env и запустить бота с вкладки «Запуск».
- CLI: .venv\Scripts\python.exe launch.py --run-bot (предварительно настроить .env). Проверка AI: launch.py --test-ai, просмотр настроек: launch.py --print-env.
5) Логи и файлы:
- Логи приложения: logs/app.log; логи лаунчера: logs/launcher.log (отображаются на вкладке «Запуск»).
- База: DB_PATH из .env (по умолчанию bot.db).
6) Проверки (в контейнере нет Windows/py -3.12, зависимости недоступны через интернет):
- py -3.12 -V — недоступно (контейнер без Windows Python Launcher).
- .venv\Scripts\python.exe -m pip install -r requirements.txt — не выполнялось (нет Windows/py -3.12 и доступа к PyPI из контейнера).
- .venv\Scripts\python.exe -c "import aiogram, pydantic, pydantic_settings; print('OK')" — не выполнялось по той же причине.
- .venv\Scripts\python.exe launch.py (GUI) — не выполнялось из-за отсутствия Windows окружения; логика запуска усилена и проверена статически.
- При наличии BOT_TOKEN: .venv\Scripts\python.exe launch.py --run-bot и /start — не выполнялось (нет токена/среды); проверка токена теперь блокирует запуск с понятной ошибкой.
- В GUI: «Сохранить .env» и «Проверить .env» — функционал реализован и протестирован локально в коде (messagebox + лог); run-time проверка требует Windows GUI.
7) Next step:
- Проверить на реальной Windows 10 с py -3.12: запустить START_LAUNCHER.bat, установить зависимости, протестировать GUI + кнопку запуска бота с валидным BOT_TOKEN и OpenAI ключом/без него.
