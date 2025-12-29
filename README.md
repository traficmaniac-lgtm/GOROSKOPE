# GOROSKOPE

Простой Telegram-бот и Tkinter UI для тестового гороскопного MVP.

## Что понадобится
- Python 3.11+
- Токен Telegram Bot (получить у [BotFather](https://t.me/BotFather) → `/newbot` → скопируйте `HTTP API token`).
- `ADMIN_TELEGRAM_ID` — ваш числовой user_id (узнать через бота [@userinfobot](https://t.me/userinfobot) или [@getmyid_bot](https://t.me/getmyid_bot)).
- Ключ OpenAI API.

## Настройка через UI
1. Создайте (по желанию) виртуальное окружение `.venv` и установите зависимости:
   ```bash
   python -m venv .venv
   .venv/Scripts/activate  # Windows PowerShell
   pip install -r requirements.txt
   ```
2. Запустите `run_ui.bat` (двойной клик) или `python -m ui.settings_ui`.
3. В окне UI заполните поля:
   - `TELEGRAM_BOT_TOKEN`
   - `OPENAI_API_KEY`
   - `OPENAI_MODEL` (по умолчанию `gpt-4o-mini`)
   - `ADMIN_TELEGRAM_ID`
4. Нажмите **Save** — будет создан/обновлён `.env`.
5. Кнопкой **Test OpenAI** отправьте тестовый запрос (ожидается ответ `OK`).
6. Кнопкой **Run Bot** можно запустить бота напрямую из UI, **Stop Bot** — остановить.

## Запуск бота напрямую
- Двойной клик по `run_bot.bat`, либо
- В терминале: `python -m app.bot`

## Логика бота (MVP)
- `/start` — приветствие, краткий FAQ и предложение выбрать знак зодиака.
- Пользователь выбирает знак кнопками. Гороскоп генерируется на один день.
- Первые 3 запроса бесплатно, затем сообщение-заглушка «Скоро подписка ✨».

## Хранилище
- `data/db.json` (создаётся автоматически) — хранит пользователей: `user_id`, `zodiac`, `birth_date` (опционально), `free_uses`, `created_at`.

## Полезно знать
- `.env` и `data/db.json` в `.gitignore` — ключи не попадут в репозиторий.
- Минимум зависимостей, OpenAI вызывается через Responses API.
