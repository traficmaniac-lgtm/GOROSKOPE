# Гороскоп Telegram Bot (MVP)

Минимальный каркас Telegram-бота на aiogram 3.x для модуля «Гороскоп».

## Быстрый старт
1. Создайте файл `.env` по примеру `.env.example` и укажите `BOT_TOKEN`.
2. Установите зависимости: `pip install -r requirements.txt`.
3. Запустите GUI-лаунчер или CLI: `python launch.py`.
4. Для прямого запуска бота без GUI: `python launch.py --run-bot`.

## Возможности
- Главное меню с разделом «Гороскоп», балансом, настройками и информацией.
- Пошаговый сбор данных для прогнозов «На сегодня» и «На неделю» через FSM.
- Проверка и списание бесплатных лимитов (3 запроса по умолчанию).
- Заглушка AIService (работает без ключей) и подготовка к OpenAI.
- Подготовленные точки для интеграции оплаты (PaymentService interface).
- GUI-лаунчер (Tkinter) для настройки .env, теста AI, симуляции сценария и управления ботом.

## Launch.py и GUI
- `python launch.py` — открывает графический лаунчер «GOROSKOPE Launcher» без необходимости BOT_TOKEN.
- `python launch.py --print-env` — выводит текущие настройки с маскировкой токенов.
- `python launch.py --test-ai` — консольный прогон промпта и StubAIService.
- `python launch.py --run-bot` — запускает бота напрямую (аналог `python bot.py`).

### Табы GUI
- **Настройки** — редактирование и валидация `.env` (BOT_TOKEN, USE_OPENAI, OPENAI_API_KEY, LOG_LEVEL, DB_PATH).
- **Тест AI** — генерация промпта и вызов текущего AI (stub/OpenAI) без Telegram.
- **Симулятор** — чат-эмулятор сценария «Гороскоп» с валидацией данных и списанием квоты в SQLite.
- **Запуск** — запуск/остановка `bot.py` в подпроцессе, просмотр логов.
- **Мини-редактор** — сохранение поверхностных правок в `bot_overrides.json` (FREE_QUOTA, тексты, стиль промпта).

## Overrides
- Пользовательские правки сохраняются в `bot_overrides.json` (значения квоты, стоимости, тексты, стиль промпта).
- `settings.py` подхватывает `OVERRIDES_PATH`, `FREE_QUOTA`, `REQUEST_PRICE_STARS`; `runtime_config` применяет JSON поверх .env.
- Тексты (`app/core/texts.py`) и `PromptBuilder` умеют читать overrides без изменения основной архитектуры.

## Стек
- Python 3.11+
- aiogram 3.x
- aiosqlite
- pydantic-settings
