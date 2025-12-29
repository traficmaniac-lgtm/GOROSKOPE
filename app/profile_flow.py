"""Conversation flow for collecting user profile data."""
from __future__ import annotations

import re
from typing import Dict

from telegram import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters

from app import storage

NAME, GENDER, BIRTH_DATE, BIRTH_TIME, CITY, SIGN, THEME = range(7)
SKIP_TEXT = "Пропустить"

GENDER_OPTIONS = ["Мужской", "Женский", SKIP_TEXT]
THEME_OPTIONS = ["отношения", "деньги", "работа", "энергия"]
ZODIAC_SIGNS = [
    "Овен",
    "Телец",
    "Близнецы",
    "Рак",
    "Лев",
    "Дева",
    "Весы",
    "Скорпион",
    "Стрелец",
    "Козерог",
    "Водолей",
    "Рыбы",
]


def _skip_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup([[KeyboardButton(SKIP_TEXT)]], resize_keyboard=True, one_time_keyboard=True)


def _choices_keyboard(options: list[str]) -> ReplyKeyboardMarkup:
    rows = [options[i : i + 2] for i in range(0, len(options), 2)]
    return ReplyKeyboardMarkup([[KeyboardButton(text=o) for o in row] for row in rows], resize_keyboard=True)


def zodiac_from_date(date_str: str) -> str:
    try:
        day, month, *_ = [int(x) for x in date_str.split(".")]
    except Exception:  # noqa: BLE001
        return ""

    # Boundaries: (month, day, sign)
    boundaries = [
        (1, 20, "Козерог"),
        (2, 19, "Водолей"),
        (3, 21, "Рыбы"),
        (4, 21, "Овен"),
        (5, 21, "Телец"),
        (6, 22, "Близнецы"),
        (7, 23, "Рак"),
        (8, 23, "Лев"),
        (9, 24, "Дева"),
        (10, 24, "Весы"),
        (11, 23, "Скорпион"),
        (12, 22, "Стрелец"),
        (12, 32, "Козерог"),
    ]
    for m, d, sign in boundaries:
        if (month, day) < (m, d):
            return sign
    return ""


def _get_draft(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Dict:
    if "profile_draft" not in context.user_data:
        user = storage.get_user(update.effective_user.id)
        context.user_data["profile_draft"] = storage.Profile.from_dict(user.get("profile"))
    return context.user_data["profile_draft"]


async def start_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    storage.get_user(update.effective_user.id)
    greeting = (
        "🔮 Добро пожаловать в GOROSKOPE!\n"
        "Я астрологичный ассистент: вдохновляю, но не обещаю чудес.\n"
        "FAQ: /today — прогноз на день, /week — на неделю, /profile или /me — профиль, /reset — сброс."
    )
    faq = "Давай настроим профиль. Можешь пропускать шаги. Как тебя зовут?"
    if update.message:
        await update.message.reply_text(f"{greeting}\n\n{faq}", reply_markup=_skip_keyboard())
    context.user_data["profile_draft"] = storage.Profile()
    return NAME


async def name_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    draft = _get_draft(update, context)
    text = (update.message.text or "").strip()
    draft.name = "" if text == SKIP_TEXT else text
    if update.message:
        await update.message.reply_text("Пол (опционально)", reply_markup=_choices_keyboard(GENDER_OPTIONS))
    return GENDER


async def gender_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    draft = _get_draft(update, context)
    text = (update.message.text or "").strip()
    draft.gender = "" if text == SKIP_TEXT else text
    if update.message:
        await update.message.reply_text("Дата рождения (дд.мм.гггг)", reply_markup=_skip_keyboard())
    return BIRTH_DATE


async def birth_date_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    draft = _get_draft(update, context)
    text = (update.message.text or "").strip()
    if text != SKIP_TEXT:
        if not re.match(r"^\d{2}\.\d{2}\.\d{4}$", text):
            if update.message:
                await update.message.reply_text(
                    "Введите дату в формате дд.мм.гггг или нажмите 'Пропустить'.",
                    reply_markup=_skip_keyboard(),
                )
            return BIRTH_DATE
        draft.birth_date = text
        auto_sign = zodiac_from_date(text)
        if auto_sign and not draft.sign:
            draft.sign = auto_sign
    if update.message:
        await update.message.reply_text(
            "Время рождения (чч:мм, можно пропустить)", reply_markup=_skip_keyboard()
        )
    return BIRTH_TIME


async def birth_time_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    draft = _get_draft(update, context)
    text = (update.message.text or "").strip()
    if text != SKIP_TEXT:
        if not re.match(r"^\d{2}:\d{2}$", text):
            if update.message:
                await update.message.reply_text(
                    "Введите время в формате чч:мм или нажмите 'Пропустить'.",
                    reply_markup=_skip_keyboard(),
                )
            return BIRTH_TIME
        draft.birth_time = text
    if update.message:
        await update.message.reply_text(
            "Город/страна рождения или текущий город", reply_markup=_skip_keyboard()
        )
    return CITY


async def city_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    draft = _get_draft(update, context)
    text = (update.message.text or "").strip()
    draft.city = "" if text == SKIP_TEXT else text
    if update.message:
        await update.message.reply_text("Твой знак зодиака?", reply_markup=_choices_keyboard(ZODIAC_SIGNS))
    return SIGN


async def sign_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    draft = _get_draft(update, context)
    text = (update.message.text or "").strip()
    if text not in ZODIAC_SIGNS:
        if update.message:
            await update.message.reply_text(
                "Пожалуйста выбери знак кнопкой ниже.", reply_markup=_choices_keyboard(ZODIAC_SIGNS)
            )
        return SIGN
    draft.sign = text
    if update.message:
        await update.message.reply_text("Выбери тему дня", reply_markup=_choices_keyboard(THEME_OPTIONS))
    return THEME


async def theme_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    draft = _get_draft(update, context)
    text = (update.message.text or "").strip().lower()
    if text not in THEME_OPTIONS:
        if update.message:
            await update.message.reply_text(
                "Используй кнопки для выбора темы.", reply_markup=_choices_keyboard(THEME_OPTIONS)
            )
        return THEME
    draft.theme = text
    storage.update_profile(update.effective_user.id, draft)

    summary = storage.profile_summary(draft)
    if update.message:
        await update.message.reply_text(
            f"Профиль сохранён!\n\n{summary}\n\nИспользуй /today или /week.",
            reply_markup=ReplyKeyboardRemove(),
        )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message:
        await update.message.reply_text(
            "Окей, профиль можно настроить позже командой /start.", reply_markup=ReplyKeyboardRemove()
        )
    return ConversationHandler.END


def build_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("start", start_profile)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name_step)],
            GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, gender_step)],
            BIRTH_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, birth_date_step)],
            BIRTH_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, birth_time_step)],
            CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, city_step)],
            SIGN: [MessageHandler(filters.TEXT & ~filters.COMMAND, sign_step)],
            THEME: [MessageHandler(filters.TEXT & ~filters.COMMAND, theme_step)],
        },
        fallbacks=[MessageHandler(filters.Regex("^/reset$"), cancel)],
        allow_reentry=True,
    )
