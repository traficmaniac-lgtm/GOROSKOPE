from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, ConversationHandler, ContextTypes, MessageHandler, filters

from handlers import shared

SUBTYPE, PERSON1, PERSON1_EXTRA, CITY1, PERSON2, PERSON2_EXTRA, CITY2, STYLE, CONFIRM = range(9)

COMPAT_TYPES = [
    ("❤️ Любовная", "love"),
    ("🤝 Деловая", "biz"),
    ("🧠 Психологическая", "psy"),
]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query:
        await update.callback_query.answer()
    buttons = [[InlineKeyboardButton(text, callback_data=f"comp:sub:{code}")] for text, code in COMPAT_TYPES]
    buttons.append([InlineKeyboardButton("🏠 Домой", callback_data="nav:home")])
    await update.effective_message.reply_text("✨ Совместимость", reply_markup=InlineKeyboardMarkup(buttons))
    return SUBTYPE


async def choose_subtype(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()
    context.user_data["compat"] = {"subtype": update.callback_query.data.split(":")[-1], "input": {}, "style": "short"}
    await update.callback_query.edit_message_text("Человек 1: дата рождения", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ Назад", callback_data="nav:home")]]))
    return PERSON1


async def set_person1(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.setdefault("compat", {}).setdefault("input", {})["person1_date"] = update.effective_message.text
    kb = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("точно", callback_data="comp:p1:exact")],
            [InlineKeyboardButton("не знаю", callback_data="comp:p1:unknown")],
            [InlineKeyboardButton("примерно", callback_data="comp:p1:approx")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="nav:home")],
        ]
    )
    await update.effective_message.reply_text("Время (1)?", reply_markup=kb)
    return PERSON1_EXTRA


async def set_person1_extra(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()
    context.user_data.setdefault("compat", {}).setdefault("input", {})["person1_time"] = update.callback_query.data.split(":")[-1]
    await update.callback_query.edit_message_text("Город (1)?", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ Назад", callback_data="nav:home")]]))
    return CITY1


async def set_city1(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.setdefault("compat", {}).setdefault("input", {})["person1_city"] = update.effective_message.text
    await update.effective_message.reply_text("Человек 2: дата рождения", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ Назад", callback_data="nav:home")]]))
    return PERSON2


async def set_person2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.setdefault("compat", {}).setdefault("input", {})["person2_date"] = update.effective_message.text
    kb = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("точно", callback_data="comp:p2:exact")],
            [InlineKeyboardButton("не знаю", callback_data="comp:p2:unknown")],
            [InlineKeyboardButton("примерно", callback_data="comp:p2:approx")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="nav:home")],
        ]
    )
    await update.effective_message.reply_text("Время (2)?", reply_markup=kb)
    return PERSON2_EXTRA


async def set_person2_extra(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()
    context.user_data.setdefault("compat", {}).setdefault("input", {})["person2_time"] = update.callback_query.data.split(":")[-1]
    await update.callback_query.edit_message_text("Город (2)?", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ Назад", callback_data="nav:home")]]))
    return CITY2


async def set_city2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.setdefault("compat", {}).setdefault("input", {})["person2_city"] = update.effective_message.text
    kb = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("коротко", callback_data="comp:style:short")],
            [InlineKeyboardButton("подробно", callback_data="comp:style:full")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="nav:home")],
        ]
    )
    await update.effective_message.reply_text("Стиль?", reply_markup=kb)
    return STYLE


async def confirm_style(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()
    context.user_data.setdefault("compat", {})["style"] = update.callback_query.data.split(":")[-1]
    data = context.user_data.get("compat", {})
    input_block = data.get("input", {})
    summary = (
        "✅ Подтверди:\n"
        f"Тип: {data.get('subtype')}\n"
        f"1: {input_block.get('person1_date')} / {input_block.get('person1_time')}\n"
        f"Город 1: {input_block.get('person1_city')}\n"
        f"2: {input_block.get('person2_date')} / {input_block.get('person2_time')}\n"
        f"Город 2: {input_block.get('person2_city')}\n"
        f"Стиль: {data.get('style')}"
    )
    buttons = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("✅ Рассчитать", callback_data="comp:go")],
            [InlineKeyboardButton("✏️ Изменить", callback_data="main:compatibility")],
            [InlineKeyboardButton("🏠 Домой", callback_data="nav:home")],
        ]
    )
    await update.effective_message.reply_text(summary, reply_markup=buttons)
    return CONFIRM


async def run_forecast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()
    data = context.user_data.get("compat", {})
    payload = {
        "user_id": update.effective_user.id,
        "mode": "compatibility",
        "subtype": data.get("subtype"),
        "input": data.get("input", {}),
        "style": data.get("style", "short"),
        "locale": "ru",
        "timezone": "Europe/Kyiv",
    }
    buttons = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("💡 Улучшить", callback_data="main:compatibility")],
            [InlineKeyboardButton("⚠️ Риски", callback_data="main:compatibility")],
            [InlineKeyboardButton("💾 История", callback_data="history:open")],
            [InlineKeyboardButton("🏠 Домой", callback_data="nav:home")],
        ]
    )
    await shared.ensure_access_or_paywall(update, context, payload, buttons)
    return ConversationHandler.END


def build_conversation() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(start, pattern=r"^main:compatibility$")],
        states={
            SUBTYPE: [CallbackQueryHandler(choose_subtype, pattern=r"^comp:sub:")],
            PERSON1: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_person1)],
            PERSON1_EXTRA: [CallbackQueryHandler(set_person1_extra, pattern=r"^comp:p1:")],
            CITY1: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_city1)],
            PERSON2: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_person2)],
            PERSON2_EXTRA: [CallbackQueryHandler(set_person2_extra, pattern=r"^comp:p2:")],
            CITY2: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_city2)],
            STYLE: [CallbackQueryHandler(confirm_style, pattern=r"^comp:style:")],
            CONFIRM: [CallbackQueryHandler(run_forecast, pattern=r"^comp:go")],
        },
        fallbacks=[CallbackQueryHandler(start, pattern=r"^main:compatibility$")],
        map_to_parent={ConversationHandler.END: ConversationHandler.END},
        allow_reentry=True,
    )

