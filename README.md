# GOROSKOPE

Telegram-бот и Tkinter UI для быстрого MVP гороскопов.

## Что понадобится
- Python 3.11+
- Токен Telegram Bot (BotFather → `/newbot` → HTTP API token)
- `ADMIN_TELEGRAM_ID` — числовой `user_id` (узнать через @getmyid_bot)
- Ключ OpenAI API (Responses API, openai>=2)

## Установка
1. (Опционально) создать виртуальное окружение `.venv` и установить зависимости:
   ```bash
   python -m venv .venv
   .venv/Scripts/activate  # Windows PowerShell
   pip install -r requirements.txt
   ```
2. Двойной клик по `run_ui.bat` (или `python -m ui.settings_ui`).
3. В UI заполнить `TELEGRAM_BOT_TOKEN`, `OPENAI_API_KEY`, `OPENAI_MODEL` (по умолчанию `gpt-4o-mini`), `ADMIN_TELEGRAM_ID` и нажать **Save**.
4. Кнопкой **Test OpenAI** отправить тест — ожидается ответ `OK`.
5. Кнопками **Run Bot / Stop Bot** запускать и останавливать бота.

Если `.venv` отсутствует, батники подскажут запустить `00_setup_repo.ps1`.

## Запуск бота напрямую
- Двойной клик по `run_bot.bat`, либо
- `python -m app.bot`

## Логика бота
- `/start` — приветствие + FAQ, далее анкета (имя, пол, дата/время рождения, город, знак, тема дня).
- `/today` — прогноз на сегодня.
- `/week` — прогноз на неделю.
- `/profile` — показать профиль и лимиты.
- `/reset` — сброс анкеты и счётчиков.
- `/grant <user_id> <days>` — продление подписки (только для `ADMIN_TELEGRAM_ID`).

Первые 3 прогноза бесплатно для каждого `user_id`. Далее — заглушка про оплату/связь. Активная подписка хранится в `sub_until` и снимает ограничения. Прогнозы генерируются через OpenAI Responses API с тёплым астрологическим тоном.

## Хранилище
- `data/db.json` (автосоздание, в .gitignore) — хранит профиль, `free_uses`, `sub_until`.

## Полезно знать
- `.env` в корне. Создаётся UI.
- Минимальный набор зависимостей: `python-telegram-bot 22.x`, `openai>=2`, `python-dotenv`.
- UI останавливает процесс бота через `terminate/kill`.
