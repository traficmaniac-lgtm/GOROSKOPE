# NOTES

## Структура
- `app/bot.py` — все команды, проверка лимитов, обращение к OpenAI.
- `app/profile_flow.py` — ConversationHandler (анкета по /start).
- `app/storage.py` — JSON-хранилище (`data/db.json`) с профилями, лимитами и подпиской.
- `app/openai_client.py` — обёртка над Responses API (`client.responses.create`).
- `ui/settings_ui.py` — Tkinter UI: редактирование `.env`, тест OpenAI, запуск/остановка бота.
- `run_bot.bat` / `run_ui.bat` — запуск с подсказкой про `00_setup_repo.ps1`, если `.venv` нет.

## OpenAI
- Используется `openai>=2`, метод `client.responses.create(model=..., input=..., max_output_tokens>=200)`.
- Тестовый запрос `Ответь коротко: OK` должен вернуть `OK`.

## Лимиты
- Каждому `user_id` доступно 3 бесплатных прогноза (`free_uses`).
- Подписка хранится в `sub_until` (unix timestamp). Команда `/grant <id> <days>` увеличивает срок.

## UI
- `.env` создаётся/обновляется через форму.
- Кнопка **Run Bot** стартует `python -m app.bot` в отдельном процессе, **Stop Bot** завершает `terminate`/`kill`.
