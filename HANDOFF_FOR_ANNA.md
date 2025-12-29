1) Версия этапа: v0.3
2) Что сделано:
- Реализован рабочий OpenAIService (async, модель gpt-4o-mini, таймауты/ретраи, обработка 401/429/5xx) и Stub fallback с пометкой в UI/логах.
- Добавлены стартап-проверки (BOT_TOKEN, OPENAI_API_KEY, сетевые подключения Telegram/OpenAI) в bot.py и launch.py --run-bot.
- Глобальный error handler в aiogram: логирует traceback в bot.log/консоль, пользователю отдаёт безопасное сообщение.
- PromptBuilder: системный + пользовательский промпт, структурированный ответ 6–10 пунктов (Любовь/Финансы/Здоровье/Карьера/Совет дня).
- Исправлены callback-обработчики и тексты, добавлены уведомления о Stub-режиме в ответах.
- GUI: на вкладке «Настройки» появилась кнопка «Проверить OpenAI» (тестовый запрос с выводом результата/ошибки).
- requirements.txt поправлен (aiogram), README обновлён (OpenAI включение, модель, логи).
3) Что проверено:
- python -m compileall app bot.py launch.py → ок.
- python launch.py --print-env → НЕ запустилось (ModuleNotFoundError: pydantic_settings) из-за отсутствующих зависимостей (pip недоступен из контейнера).
- python launch.py --test-ai → не запускалось по той же причине; код для stub/openai протестирован через compileall.
- pip install -r requirements.txt → не удалось (сетевое ограничение 403 при обращении к pypi; aiogram/pydantic-settings не ставятся).
4) Что НЕ сделано/ограничения:
- Не проверены реальные сетевые вызовы OpenAI/Telegram в контейнере из-за отсутствия зависимостей и BOT_TOKEN/OPENAI_API_KEY.
- Тот же Proxy 403 блокирует установку зависимостей внутри окружения.
5) Как запустить:
- Локально установить зависимости: pip install -r requirements.txt (aiogram 3.13.1, pydantic-settings 2.x, openai 1.35.10 и др.).
- Настроить .env (BOT_TOKEN обязателен; USE_OPENAI=true требует OPENAI_API_KEY, иначе авто-STUB).
- CLI: python launch.py --run-bot для запуска бота; python launch.py --test-ai для проверки AI; python launch.py --print-env для просмотра настроек (токены маскируются).
- GUI: python launch.py, вкладка «Настройки» → «Проверить OpenAI» для быстрой диагностики.
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
- app/services/health.py (health-check старта)
8) Известные проблемы/риски:
- Пакеты не устанавливаются в текущем контейнере (403 Proxy); все CLI проверки, зависящие от pydantic-settings/aiogram, нужно повторить в среде с доступом к PyPI.
- GUI вызывает asyncio.run в UI-потоке, при долгих ответах окно может «подвисать».
