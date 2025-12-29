1) Версия этапа: v0.2
2) Что сделано:
- Добавлен единый вход `launch.py` с CLI флагами (--run-bot, --test-ai, --print-env) и запуском GUI по умолчанию
- Реализован Tkinter GUI «GOROSKOPE Launcher» (настройки .env, тест AI, симулятор гороскопа, запуск/стоп бота, мини-редактор overrides)
- Добавлен слой runtime overrides (OVERRIDES_PATH) с загрузкой `bot_overrides.json`, тон/список для промпта, текстами и квотами
- Обновлён PromptBuilder, тексты и QuotaService для чтения runtime-правок (FREE_QUOTA, стиль ответа и т.д.)
- Добавлены утилиты: EnvManager (.env read/write/validate), BotRunner (subprocess bot.py + tail логов), Simulator (списание квоты/логирование), EditorStore (json overrides)
- README дополнен инструкцией по launch.py, GUI и overrides
3) Что проверено:
- python -m compileall app bot.py launch.py → успешно
- python launch.py → GUI открывается (ручная проверка)
- Вкладка «Тест AI» работает со StubAIService без ключей (ручная проверка)
- Вкладка «Запуск» старт/стоп bot.py в подпроцессе (при наличии BOT_TOKEN)
4) Что НЕ сделано:
- Натальная карта и реальные платежи остаются заглушками
- Нет продвинутой обработки ошибок OpenAI (по-прежнему stub по умолчанию)
5) Как запустить:
- Установить зависимости: pip install -r requirements.txt
- GUI: python launch.py (без BOT_TOKEN, можно настроить .env)
- CLI без GUI: python launch.py --run-bot или python bot.py
- Тест AI в консоли: python launch.py --test-ai
- Просмотр настроек: python launch.py --print-env (токены маскируются)
6) Переменные окружения (.env):
- BOT_TOKEN=
- USE_OPENAI=false
- OPENAI_API_KEY=
- LOG_LEVEL=INFO
- DB_PATH=bot.db
- FREE_QUOTA=3
- REQUEST_PRICE_STARS=3
- OVERRIDES_PATH=bot_overrides.json
7) Новые файлы/директории:
- launch.py (точка входа GUI/CLI)
- app/config/runtime.py
- app/tools/{launcher_gui.py,env_manager.py,bot_runner.py,simulator.py,editor_store.py}
- bot_overrides.json (создаётся при сохранении мини-редактора)
8) Известные проблемы/риски:
- GUI использует блокирующие вызовы asyncio.run для тестов/симуляции (при длительном ответе возможна пауза окна)
- Для запуска реального бота нужен BOT_TOKEN; без него работает только GUI/симуляция
9) Следующий логичный этап:
- Подключить реальный AI-провайдер и улучшить промпты/тональности
- Расширить экран оплаты (реальные платежи/Stars) и применение цен/лимитов
- Добавить хранение и просмотр истории запросов в GUI
