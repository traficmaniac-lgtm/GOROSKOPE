from app.config.runtime import runtime_config

WELCOME = (
    "Привет! Я бот 'Гороскоп'. Помогу получить прогноз. Выберите раздел в меню ниже."
)
ABOUT = "Бот для получения гороскопов. Используется aiogram 3.x и SQLite."
SETTINGS = "Настройки и проверки подключения OpenAI находятся здесь."
BALANCE = "Ваш баланс бесплатных запросов: {free_left}"
LIMIT_REACHED = (
    "Вы исчерпали бесплатные запросы. Можно будет купить дополнительный запрос или оформить подписку."
)
ASK_BIRTH_DATE = "Введите дату рождения в формате ДД.ММ.ГГГГ"
ASK_TIME_KNOWN = "Знаете ли вы точное время рождения?"
ASK_BIRTH_TIME = "Введите время рождения в формате ЧЧ:ММ"
ASK_BIRTH_PLACE = "Введите место рождения"
ASK_GENDER = "Выберите ваш пол"
ASK_FOCUS = "Какой аспект интересует?"
INVALID_DATE = "Неверный формат даты. Используйте ДД.ММ.ГГГГ"
INVALID_TIME = "Неверный формат времени. Используйте ЧЧ:ММ"
NATAL_SOON = "Натальная карта скоро будет доступна."
PROCESSING = "Готовлю ваш прогноз..."
GENERATION_ERROR = "Не удалось получить ответ. Попробуйте позже."
GENERATION_STUB_NOTICE = "Бот работает в демо-режиме (OpenAI отключён)."


def _apply_overrides() -> None:
    overrides = runtime_config.text_overrides
    for key, value in overrides.items():
        if key in globals():
            globals()[key] = value


_apply_overrides()
