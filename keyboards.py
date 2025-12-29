from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

MAIN_MENU = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("🔮 Гороскоп", callback_data="module:horoscope")],
        [InlineKeyboardButton("🃏 Таро", callback_data="module:tarot")],
        [InlineKeyboardButton("🔢 Нумерология", callback_data="module:numerology")],
        [InlineKeyboardButton("❤️ Совместимость", callback_data="module:compat")],
        [
            InlineKeyboardButton("👤 Профиль", callback_data="menu:profile"),
            InlineKeyboardButton("⭐ Премиум-доступ", callback_data="menu:premium"),
        ],
        [InlineKeyboardButton("🎁 Бонусы", callback_data="menu:bonus")],
        [InlineKeyboardButton("📌 Избранное", callback_data="menu:favorites")],
        [InlineKeyboardButton("🆘 Помощь", callback_data="menu:help")],
        [InlineKeyboardButton("⚙️ Настройки", callback_data="menu:settings")],
        [InlineKeyboardButton("ℹ️ О проекте", callback_data="menu:about")],
    ]
)

HOROSCOPE_TYPES = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("☀️ Сегодня", callback_data="sub:horoscope:today")],
        [InlineKeyboardButton("🌙 Завтра", callback_data="sub:horoscope:tomorrow")],
        [InlineKeyboardButton("📅 Неделя", callback_data="sub:horoscope:week")],
        [InlineKeyboardButton("🧭 Месяц", callback_data="sub:horoscope:month")],
        [InlineKeyboardButton("✨ Персональный (⭐)", callback_data="sub:horoscope:personal")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="nav:home")],
    ]
)

TAROT_TYPES = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("🔮 Одна карта", callback_data="sub:tarot:one_card")],
        [InlineKeyboardButton("🃏 Три карты", callback_data="sub:tarot:three_cards")],
        [InlineKeyboardButton("🕯️ Да/Нет", callback_data="sub:tarot:yes_no")],
        [InlineKeyboardButton("💞 Отношения", callback_data="sub:tarot:love")],
        [InlineKeyboardButton("💼 Работа и деньги", callback_data="sub:tarot:career")],
        [InlineKeyboardButton("⭐ Глубокий расклад", callback_data="sub:tarot:deep")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="nav:home")],
    ]
)

NUMEROLOGY_TYPES = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("🔢 Число судьбы", callback_data="sub:numerology:destiny")],
        [InlineKeyboardButton("📅 Число дня", callback_data="sub:numerology:day")],
        [InlineKeyboardButton("🧬 Кармические задачи", callback_data="sub:numerology:karma")],
        [InlineKeyboardButton("🧠 Личностный код (⭐)", callback_data="sub:numerology:personality")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="nav:home")],
    ]
)

COMPAT_TYPES = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("💞 Любовь", callback_data="sub:compat:love")],
        [InlineKeyboardButton("🤝 Дружба", callback_data="sub:compat:friend")],
        [InlineKeyboardButton("💼 Бизнес", callback_data="sub:compat:business")],
        [InlineKeyboardButton("⭐ Полный отчёт", callback_data="sub:compat:full")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="nav:home")],
    ]
)

BACK_MENU = InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Меню", callback_data="nav:home")]])
