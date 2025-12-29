from __future__ import annotations

from typing import List

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from app import storage

MAIN_TITLE = "🪐 Главное меню"
START_INTRO = "Я — астрологический ассистент. Давай начнём?"


def _row(*buttons: InlineKeyboardButton) -> List[InlineKeyboardButton]:
    return list(buttons)


def _nav_row() -> List[InlineKeyboardButton]:
    return _row(
        InlineKeyboardButton("⬅️ Назад", callback_data="nav:back"),
        InlineKeyboardButton("🏠 Меню", callback_data="nav:home"),
    )


def build_main_keyboard(is_new_user: bool) -> InlineKeyboardMarkup:
    rows: List[List[InlineKeyboardButton]] = [
        _row(
            InlineKeyboardButton("🔮 Гороскоп", callback_data="menu:horoscope"),
            InlineKeyboardButton("🃏 Таро", callback_data="menu:tarot"),
        ),
        _row(
            InlineKeyboardButton("🔢 Нумерология", callback_data="menu:numerology"),
            InlineKeyboardButton("❤️ Совместимость", callback_data="menu:compat"),
        ),
        _row(InlineKeyboardButton("👤 Профиль", callback_data="menu:profile")),
        _row(
            InlineKeyboardButton("⭐ Премиум-доступ", callback_data="paywall:open"),
            InlineKeyboardButton("🎁 Бонусы", callback_data="bonus:open"),
        ),
        _row(
            InlineKeyboardButton("📌 Избранное", callback_data="fav:open"),
            InlineKeyboardButton("🆘 Помощь", callback_data="help:open"),
        ),
        _row(
            InlineKeyboardButton("⚙️ Настройки", callback_data="settings:open"),
            InlineKeyboardButton("ℹ️ О проекте", callback_data="about:open"),
        ),
        _nav_row(),
    ]

    if is_new_user:
        rows.insert(
            2,
            _row(
                InlineKeyboardButton("⚡ Настроить профиль", callback_data="menu:profile"),
                InlineKeyboardButton("🚀 Быстрый старт", callback_data="menu:horoscope"),
            ),
        )

    return InlineKeyboardMarkup(rows)


async def render_start_screen(
    update: Update, context: ContextTypes.DEFAULT_TYPE, is_new_user: bool
) -> None:
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🚀 Перейти в меню", callback_data="nav:home")],
            [InlineKeyboardButton("⚡ Настроить профиль", callback_data="menu:profile")],
        ]
    )
    message = update.effective_message
    intro = "GOROSKOPE — платный AI-гороскоп с Premium через Stars."
    if message:
        await message.reply_text(f"{START_INTRO}\n{intro}", reply_markup=keyboard)


async def render_main_menu(
    update: Update, context: ContextTypes.DEFAULT_TYPE, is_new_user: bool
) -> None:
    keyboard = build_main_keyboard(is_new_user)
    message = update.effective_message

    if update.callback_query:
        await update.callback_query.answer()
        if message:
            try:
                await message.edit_text(MAIN_TITLE, reply_markup=keyboard)
            except Exception:  # noqa: BLE001
                await message.edit_reply_markup(reply_markup=keyboard)
        return

    if message:
        await message.reply_text(MAIN_TITLE, reply_markup=keyboard)


async def render_horoscope_menu(update: Update) -> None:
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🌞 Сегодня", callback_data="horoscope:today")],
            [InlineKeyboardButton("🌙 Завтра", callback_data="horoscope:tomorrow")],
            [InlineKeyboardButton("📅 Неделя", callback_data="horoscope:week")],
            [InlineKeyboardButton("🧭 Месяц", callback_data="horoscope:month")],
            [InlineKeyboardButton("🌌 Персональный (⭐)", callback_data="paywall:open")],
            _nav_row(),
        ]
    )
    query = update.callback_query
    if query:
        await query.answer()
        if update.effective_message:
            await update.effective_message.edit_text(
                "🔮 Выбери формат прогноза", reply_markup=keyboard
            )


async def render_tarot_menu(update: Update) -> None:
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🔮 Одна карта", callback_data="tarot:one")],
            [InlineKeyboardButton("🃏 Три карты", callback_data="tarot:three")],
            [InlineKeyboardButton("🕯 Да / Нет", callback_data="tarot:yesno")],
            [InlineKeyboardButton("💞 Отношения", callback_data="tarot:love")],
            [InlineKeyboardButton("💼 Работа и деньги", callback_data="tarot:work")],
            [InlineKeyboardButton("⭐ Глубокий расклад", callback_data="paywall:open")],
            _nav_row(),
        ]
    )
    query = update.callback_query
    if query:
        await query.answer()
        if update.effective_message:
            await update.effective_message.edit_text(
                "🃏 Выбери расклад", reply_markup=keyboard
            )


async def render_numerology_menu(update: Update) -> None:
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🔢 Число судьбы", callback_data="num:destiny")],
            [InlineKeyboardButton("📆 Число дня", callback_data="num:day")],
            [InlineKeyboardButton("🧬 Кармические задачи", callback_data="num:karma")],
            [InlineKeyboardButton("🧠 Личностный код (⭐)", callback_data="paywall:open")],
            _nav_row(),
        ]
    )
    query = update.callback_query
    if query:
        await query.answer()
        if update.effective_message:
            await update.effective_message.edit_text(
                "🔢 Нумерологический анализ", reply_markup=keyboard
            )


async def render_compat_menu(update: Update) -> None:
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("💞 Любовь", callback_data="compat:love")],
            [InlineKeyboardButton("🤝 Дружба", callback_data="compat:friend")],
            [InlineKeyboardButton("💼 Бизнес", callback_data="compat:biz")],
            [InlineKeyboardButton("⭐ Полный отчёт", callback_data="paywall:open")],
            _nav_row(),
        ]
    )
    query = update.callback_query
    if query:
        await query.answer()
        if update.effective_message:
            await update.effective_message.edit_text(
                "❤️ Анализ совместимости", reply_markup=keyboard
            )


async def render_profile(update: Update) -> None:
    query = update.callback_query
    if query:
        await query.answer()

    user = storage.get_user(update.effective_user.id)
    profile = storage.Profile.from_dict(user.get("profile"))
    summary = storage.profile_summary(profile)
    premium = "⭐ Premium активен" if storage.has_premium(user) else "Без Premium"
    message = update.effective_message
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("✏️ Изменить данные", callback_data="menu:profile:edit")],
            [InlineKeyboardButton("🌟 Premium статус", callback_data="paywall:open")],
            [InlineKeyboardButton("🗑 Сброс профиля", callback_data="menu:profile:reset")],
            _nav_row(),
        ]
    )
    if message:
        await message.edit_text(
            f"👤 Профиль\n{summary}\n{premium}", reply_markup=keyboard
        )


async def render_premium(update: Update) -> None:
    query = update.callback_query
    if query:
        await query.answer()
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("⭐ Купить за Stars", callback_data="paywall:open")],
            [InlineKeyboardButton("🎁 Пробный бонус", callback_data="bonus:open")],
            _nav_row(),
        ]
    )
    if update.effective_message:
        await update.effective_message.edit_text(
            "⭐ Premium доступ\nПолные расклады, глубокие прогнозы, персональные советы.",
            reply_markup=keyboard,
        )


async def render_bonuses(update: Update) -> None:
    query = update.callback_query
    if query:
        await query.answer()
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🎁 Ежедневный бонус", callback_data="bonus:daily")],
            [InlineKeyboardButton("🤝 Пригласить друга", callback_data="bonus:invite")],
            [InlineKeyboardButton("🃏 Бесплатный расклад", callback_data="tarot:one")],
            _nav_row(),
        ]
    )
    if update.effective_message:
        await update.effective_message.edit_text("🎁 Бонусы", reply_markup=keyboard)


async def render_favorites(update: Update) -> None:
    if update.callback_query:
        await update.callback_query.answer()
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📜 История", callback_data="fav:history")],
        [InlineKeyboardButton("🧹 Очистить", callback_data="fav:clear")],
        _nav_row(),
    ])
    if update.effective_message:
        await update.effective_message.edit_text("📌 Избранное", reply_markup=keyboard)


async def render_settings(update: Update) -> None:
    if update.callback_query:
        await update.callback_query.answer()
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🌍 Язык", callback_data="settings:lang")],
            [InlineKeyboardButton("🔔 Уведомления", callback_data="settings:notify")],
            [InlineKeyboardButton("🕒 Часовой пояс", callback_data="settings:tz")],
            _nav_row(),
        ]
    )
    if update.effective_message:
        await update.effective_message.edit_text("⚙️ Настройки", reply_markup=keyboard)


async def render_help(update: Update) -> None:
    if update.callback_query:
        await update.callback_query.answer()
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("❓ FAQ", callback_data="help:faq")],
            [InlineKeyboardButton("💬 Связь", url="https://t.me/")],
            [InlineKeyboardButton("⭐ Как работает Premium", callback_data="paywall:features")],
            _nav_row(),
        ]
    )
    if update.effective_message:
        await update.effective_message.edit_text("🆘 Помощь", reply_markup=keyboard)


async def render_about(update: Update) -> None:
    if update.callback_query:
        await update.callback_query.answer()
    text = (
        "ℹ️ GOROSKOPE — AI-астрологический сервис."
        " Не медицинская или юридическая консультация."
        " Мы за прозрачность и ценность в каждом прогнозе."
    )
    if update.effective_message:
        await update.effective_message.edit_text(text, reply_markup=InlineKeyboardMarkup([_nav_row()]))


async def respond_placeholder(update: Update, text: str) -> None:
    query = update.callback_query
    if query:
        await query.answer(text=text, show_alert=False)
