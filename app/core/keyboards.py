from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔮 Гороскоп", callback_data="menu_horoscope")],
            [InlineKeyboardButton(text="⭐ Баланс", callback_data="menu_balance")],
            [InlineKeyboardButton(text="⚙️ Настройки", callback_data="menu_settings")],
            [InlineKeyboardButton(text="ℹ️ О проекте", callback_data="menu_about")],
        ]
    )


def horoscope_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="☀️ На сегодня", callback_data="hs_today")],
            [InlineKeyboardButton(text="📆 На неделю", callback_data="hs_week")],
            [InlineKeyboardButton(text="🧬 Натальная карта", callback_data="hs_natal")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main")],
        ]
    )


def time_known_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Знаю", callback_data="time_yes"),
                InlineKeyboardButton(text="Не знаю", callback_data="time_no"),
            ]
        ]
    )


def gender_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="М", callback_data="gender_m"),
                InlineKeyboardButton(text="Ж", callback_data="gender_f"),
                InlineKeyboardButton(text="Другое", callback_data="gender_o"),
            ]
        ]
    )


def focus_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Любовь", callback_data="focus_love"), InlineKeyboardButton(text="Финансы", callback_data="focus_money")],
            [InlineKeyboardButton(text="Здоровье", callback_data="focus_health"), InlineKeyboardButton(text="Карьера", callback_data="focus_career")],
            [InlineKeyboardButton(text="Общее", callback_data="focus_general")],
        ]
    )


def limit_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⭐ Купить запрос", callback_data="limit_buy")],
            [InlineKeyboardButton(text="💎 Подписка", callback_data="limit_sub")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_horoscope")],
        ]
    )


def result_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔁 Сгенерировать заново", callback_data="regen")],
            [InlineKeyboardButton(text="🏠 В главное меню", callback_data="back_main")],
        ]
    )
