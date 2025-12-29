# GOROSKOPE

Минимальный Telegram-бот с настройщиком на Tkinter для проверки подключения OpenAI.

## Подготовка
1. Создайте бота через BotFather и получите `TELEGRAM_BOT_TOKEN`.
2. Получите `OPENAI_API_KEY` в кабинете OpenAI и при необходимости укажите модель (по умолчанию `gpt-4o-mini`).
3. Распакуйте проект на Windows 10 и при желании создайте виртуальное окружение `.venv`.
4. Установите зависимости:
   ```powershell
   pip install -r requirements.txt
   ```

## Настройка через UI
1. Запустите `run_ui.bat` (использует `.venv\Scripts\python.exe`, если есть, иначе системный `python`).
2. Введите значения:
   - `TELEGRAM_BOT_TOKEN`
   - `OPENAI_API_KEY`
   - `OPENAI_MODEL` (оставьте `gpt-4o-mini`, если не уверены)
   - `ADMIN_TELEGRAM_ID` (необязательно)
3. Нажмите **Save** — создаст/обновит файл `.env` с нужным форматом:
   ```
   TELEGRAM_BOT_TOKEN=
   OPENAI_API_KEY=
   OPENAI_MODEL=gpt-4o-mini
   ADMIN_TELEGRAM_ID=
   TIMEZONE=Europe/Kyiv
   ```
4. Нажмите **Test OpenAI**, чтобы отправить короткий запрос «приветствие» и увидеть ответ в логе UI.
5. Нажмите **Run Bot**, чтобы запустить Telegram-бота (кнопка **Stop Bot** завершит процесс).

## Telegram-бот
- Запускается через `run_bot.bat` или из UI.
- Команды:
  - `/start` — проверка, что бот онлайн, подсказка про /ping и /ai.
  - `/ping` — отвечает `pong`.
  - `/ai` — просит текст, отправляет в OpenAI и возвращает ответ.
- Если ключи не заданы, бот подскажет заполнить `.env` через UI.

## Один клик
- `run_ui.bat` — старт настроек.
- `run_bot.bat` — прямой запуск бота.
- `launcher.bat` — меню для выбора UI или бота.
