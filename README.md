# GOROSKOPE

Telegram-бот и Tkinter UI для быстрого MVP гороскопов.

## Что понадобится
- Windows 10+
- Python 3.11+
- Токен Telegram Bot (BotFather → `/newbot` → HTTP API token)
- `ADMIN_TELEGRAM_ID` — числовой `user_id` (узнать через @getmyid_bot)
- Ключ OpenAI API (Responses API, openai>=2)

## Быстрый старт на Windows
1. Склонируйте репозиторий и откройте папку `GOROSKOPE`.
2. Дважды кликните `launcher.bat` и выберите **Run UI** (или запустите `run_ui.bat`).
3. В появившемся окне заполните `TELEGRAM_BOT_TOKEN`, `OPENAI_API_KEY`, при необходимости модель (`gpt-4o-mini` по умолчанию) и `ADMIN_TELEGRAM_ID`, затем нажмите **Save**.
4. Нажмите **Test OpenAI** — должно вернуться `OK`. Если `.venv` отсутствует, запустите PowerShell команду `python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt` и попробуйте снова.
5. Запустите бота кнопкой **Run Bot** (остановка — **Stop Bot**). Альтернатива: `run_bot.bat` или команда `python -m app.bot` из активированного окружения.

## Логика бота
- `/start` — приветствие + FAQ, далее анкета (имя, пол, дата/время рождения, город, знак, тема дня).
- `/today` — прогноз на сегодня.
- `/week` — прогноз на неделю.
- `/profile` или `/me` — показать профиль и лимиты.
- `/reset` — сброс анкеты и счётчиков.
- `/grant <user_id> <days>` — продление подписки (только для `ADMIN_TELEGRAM_ID`).

Первые 3 прогноза бесплатно для каждого `user_id`. Далее — заглушка про оплату/связь. Активная подписка хранится в `sub_until` и снимает ограничения. Прогнозы генерируются через OpenAI Responses API с тёплым астрологическим тоном.

## Хранилище
- `data/db.json` (автосоздание, в .gitignore) — хранит профиль, `free_uses`, `sub_until`.

## Полезно знать
- `.env` в корне. Создаётся UI.
- Минимальный набор зависимостей: `python-telegram-bot 22.x`, `openai>=2`, `python-dotenv`.
- UI останавливает процесс бота через `terminate/kill`.
