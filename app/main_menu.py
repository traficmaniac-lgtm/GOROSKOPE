"""Main menu layout and handlers for the Telegram bot."""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes

from app import profile_flow, storage

MenuHandler = Callable[[Update, ContextTypes.DEFAULT_TYPE], None]


@dataclass(frozen=True)
class MenuButton:
    action: str
    labels: Dict[str, List[str]]  # locale -> variants

    def title(self, locale: str) -> str:
        variants = self.labels.get(locale) or self.labels.get("ru") or []
        return random.choice(variants) if variants else self.action


MAIN_HEADER = {
    "ru": "✨ Добро пожаловать в AstroAI ✨\nИскусственный интеллект, который читает судьбу по звёздам\n\nВыберите, с чего начать ⬇️",
}

BUTTONS: list[MenuButton] = [
    MenuButton("calculate", {"ru": ["🔮 Рассчитать гороскоп", "🔮 Рассчитать судьбу"]}),
    MenuButton("self", {"ru": ["🧬 Узнать о себе", "🧬 Профиль души"]}),
    MenuButton("compatibility", {"ru": ["❤️ Совместимость", "❤️ Пара и судьба"]}),
    MenuButton("today", {"ru": ["🌙 Прогноз на сегодня", "🌙 Сегодня"]}),
    MenuButton("path", {"ru": ["🧿 Мой путь и предназначение"]}),
    MenuButton("natal", {"ru": ["📊 Натальная карта (профи)"]}),
    MenuButton("premium", {"ru": ["⭐ Премиум-разбор", "⭐ Премиум"]}),
    MenuButton("shop", {"ru": ["💫 Магазин прогнозов", "💫 Astro-шоп"]}),
    MenuButton("how", {"ru": ["ℹ️ Как это работает", "ℹ️ Гид по AstroAI"]}),
    MenuButton("settings", {"ru": ["⚙️ Настройки", "⚙️ Сервис"]}),
]

BACK_BUTTON = MenuButton("back", {"ru": ["⬅️ Назад"]})


def _chunk_buttons(buttons: Iterable[InlineKeyboardButton], size: int = 2) -> list[list[InlineKeyboardButton]]:
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for btn in buttons:
        row.append(btn)
        if len(row) == size:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return rows


def build_keyboard(locale: str = "ru") -> InlineKeyboardMarkup:
    inline_buttons = [
        InlineKeyboardButton(text=button.title(locale), callback_data=f"action:{button.action}")
        for button in BUTTONS
    ]
    rows = _chunk_buttons(inline_buttons)
    rows.append([InlineKeyboardButton(text=BACK_BUTTON.title(locale), callback_data="action:back")])
    return InlineKeyboardMarkup(rows)


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if update.callback_query:
        await update.callback_query.answer()
    if message:
        await message.reply_text(MAIN_HEADER.get("ru", ""), reply_markup=build_keyboard())


async def _reply_wait(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
    if update.callback_query:
        await update.callback_query.answer(text="⏳✨")
    message = update.effective_message
    if message:
        await message.reply_text(f"⏳✨ {text}")


async def _update_choice(update: Update, action: str) -> None:
    user_id = update.effective_user.id if update.effective_user else None
    if user_id:
        storage.update_last_choice(user_id, action)


async def _calculate_horoscope(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _reply_wait(update, context, "Запускаю мастер расчёта")
    await _update_choice(update, "calculate")
    await profile_flow.start_profile(update, context)


async def _self_insight(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _reply_wait(update, context, "Готовлю психо-портрет")
    await _update_choice(update, "self")
    message = update.effective_message
    if message:
        await message.reply_text(
            "🧬 Твои сильные стороны и кармические задачи.\n"
            "Базовый обзор — бесплатно, полный разбор за ⭐.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="⭐ Разблокировать", callback_data="action:premium")]]
            ),
        )


async def _compatibility(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _reply_wait(update, context, "Собираю данные пары")
    await _update_choice(update, "compatibility")
    message = update.effective_message
    if message:
        await message.reply_text(
            "❤️ Введи данные второго человека.\n"
            "Дам процент совместимости + краткий абзац. Глубже — за ⭐.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="⭐ Глубокий разбор", callback_data="action:premium")]]
            ),
        )


async def _today(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _reply_wait(update, context, "Считываю звёзды на сегодня")
    await _update_choice(update, "today")
    message = update.effective_message
    if message:
        await message.reply_text(
            "🌙 Короткий прогноз бесплатно.\n"
            "Хочешь полный на день?", reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="⭐ Полный прогноз", callback_data="action:premium")]]
            )
        )


async def _path(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _reply_wait(update, context, "Ищу твой путь")
    await _update_choice(update, "path")
    message = update.effective_message
    if message:
        await message.reply_text(
            "🧿 Готовлю взгляд в предназначение.\n"
            "Глубина зависит от данных профиля — начнём?",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="🔮 Заполнить профиль", callback_data="action:calculate")]]
            ),
        )


async def _natal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _reply_wait(update, context, "Открываю PRO предпросмотр")
    await _update_choice(update, "natal")
    message = update.effective_message
    if message:
        await message.reply_text(
            "📊 Натальная карта (PRO). Предпросмотр доступен, полный доступ за ⭐.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="⭐ Разблокировать PRO", callback_data="action:premium")]]
            ),
        )


async def _premium(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _reply_wait(update, context, "Подбираю пакеты")
    await _update_choice(update, "premium")
    message = update.effective_message
    if message:
        await message.reply_text(
            "⭐ Выбери пакет доступа:",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton(text="⭐ 1 день", callback_data="action:premium:1")],
                    [InlineKeyboardButton(text="⭐ 7 дней", callback_data="action:premium:7")],
                    [InlineKeyboardButton(text="⭐ Навсегда", callback_data="action:premium:forever")],
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="action:back")],
                ]
            ),
        )


async def _shop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _reply_wait(update, context, "Открываю магазин")
    await _update_choice(update, "shop")
    message = update.effective_message
    if message:
        await message.reply_text(
            "💫 Выбери готовый прогноз:",
            reply_markup=InlineKeyboardMarkup(
                _chunk_buttons(
                    [
                        InlineKeyboardButton(text="💰 Деньги", callback_data="action:shop:money"),
                        InlineKeyboardButton(text="💖 Любовь", callback_data="action:shop:love"),
                        InlineKeyboardButton(text="🚀 Карьера", callback_data="action:shop:career"),
                        InlineKeyboardButton(text="🧳 Переезд", callback_data="action:shop:move"),
                        InlineKeyboardButton(text="🗓 2025 год", callback_data="action:shop:2025"),
                    ]
                )
                + [[InlineKeyboardButton(text="⬅️ Назад", callback_data="action:back")]]
            ),
        )


async def _how(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _reply_wait(update, context, "Рассказываю правила")
    await _update_choice(update, "how")
    message = update.effective_message
    if message:
        await message.reply_text(
            "ℹ️ Я — ИИ-астролог. Сначала собираю твои данные, потом даю прогнозы."
            " Без обещаний, только мягкие рекомендации.",
        )


async def _settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _reply_wait(update, context, "Открываю настройки")
    await _update_choice(update, "settings")
    message = update.effective_message
    if message:
        await message.reply_text("⚙️ Здесь скоро появятся личные настройки и язык (RU / EN).")


ACTION_MAP: dict[str, MenuHandler] = {
    "calculate": _calculate_horoscope,
    "self": _self_insight,
    "compatibility": _compatibility,
    "today": _today,
    "path": _path,
    "natal": _natal,
    "premium": _premium,
    "shop": _shop,
    "how": _how,
    "settings": _settings,
    "back": show_main_menu,
}


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query:
        await query.answer()
        action = (query.data or "").replace("action:", "", 1)
        action_key = action.split(":", maxsplit=1)[0]
        handler = ACTION_MAP.get(action_key)
        if handler:
            await handler(update, context)
        else:
            await show_main_menu(update, context)


def build_handlers() -> list:
    return [
        CommandHandler("start", show_main_menu),
        CallbackQueryHandler(handle_callback, pattern=r"^action:"),
    ]
