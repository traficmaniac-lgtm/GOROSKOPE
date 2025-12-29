from __future__ import annotations

import logging
import random
from datetime import datetime
from typing import Dict

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

import config
import db
import texts
from handlers import compatibility, horoscope, numerology, tarot
from handlers import payments as pay
from handlers import profile as profile_handler
import keyboards

logger = logging.getLogger(__name__)

STATE_SELECT = config.FLOW_STATES["SELECT"]
STATE_INPUT1 = config.FLOW_STATES["INPUT_1"]
STATE_INPUT2 = config.FLOW_STATES["INPUT_2"]
STATE_PREVIEW = config.FLOW_STATES["PREVIEW"]
STATE_PAYWALL = config.FLOW_STATES["PAYWALL"]
STATE_RESULT = config.FLOW_STATES["RESULT"]


MODULE_MAP = {
    "horoscope": horoscope.HOROSCOPE_SUBTYPES,
    "tarot": tarot.TAROT_SUBTYPES,
    "numerology": numerology.NUMEROLOGY_SUBTYPES,
    "compat": compatibility.COMPAT_SUBTYPES,
}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    db.init_db()
    await update.effective_message.reply_text(texts.WELCOME, reply_markup=keyboards.MAIN_MENU)
    return ConversationHandler.END


async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query:
        await update.callback_query.answer()
    await update.effective_message.reply_text("Главное меню", reply_markup=keyboards.MAIN_MENU)
    return ConversationHandler.END


async def handle_module(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if not query:
        return ConversationHandler.END
    await query.answer()
    module = query.data.split(":", 1)[1]
    context.user_data["flow"] = {"module": module, "inputs": {}}
    if module == "horoscope":
        await query.edit_message_text("Выберите период", reply_markup=keyboards.HOROSCOPE_TYPES)
    elif module == "tarot":
        await query.edit_message_text("Выбери расклад", reply_markup=keyboards.TAROT_TYPES)
    elif module == "numerology":
        await query.edit_message_text("Выбери расчёт", reply_markup=keyboards.NUMEROLOGY_TYPES)
    elif module == "compat":
        await query.edit_message_text("Выбери формат", reply_markup=keyboards.COMPAT_TYPES)
    return STATE_SELECT


async def handle_subtype(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    _, module, subtype = query.data.split(":", 2)
    flow = context.user_data.get("flow", {})
    flow.update({"module": module, "subtype": subtype, "inputs": flow.get("inputs", {})})
    context.user_data["flow"] = flow
    prompt = "Укажи детали запроса"
    if module == "horoscope":
        prompt = "Давай дату рождения (ДД.ММ.ГГГГ)"
    elif module == "tarot":
        prompt = "Введи свой вопрос для расклада"
    elif module == "numerology":
        prompt = "Введи дату рождения"
    elif module == "compat":
        prompt = "Данные первого человека: имя и дата рождения"
    await query.edit_message_text(prompt, reply_markup=keyboards.BACK_MENU)
    return STATE_INPUT1


async def collect_input1(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    flow = context.user_data.get("flow", {})
    text = update.effective_message.text
    module = flow.get("module")
    if module == "compat":
        flow.setdefault("inputs", {})["person_1"] = {"raw": text}
        prompt = "Данные второго человека: имя и дата рождения"
        await update.effective_message.reply_text(prompt, reply_markup=keyboards.BACK_MENU)
        context.user_data["flow"] = flow
        return STATE_INPUT2
    flow.setdefault("inputs", {})["input_1"] = text
    prompt = "Добавь дополнительный контекст или нажми Получить" if module == "tarot" else "Можешь добавить детали (город, цель)"
    await update.effective_message.reply_text(prompt, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Пропустить", callback_data="skip:input2")]]))
    context.user_data["flow"] = flow
    return STATE_INPUT2


async def collect_input2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    flow = context.user_data.get("flow", {})
    text = update.effective_message.text
    flow.setdefault("inputs", {})["input_2"] = text
    context.user_data["flow"] = flow
    return await show_preview(update, context)


async def skip_input2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query:
        await update.callback_query.answer()
    return await show_preview(update, context)


def build_preview(flow: Dict) -> str:
    module = flow.get("module")
    if module == "horoscope":
        return horoscope.build_preview(flow)
    if module == "tarot":
        return tarot.build_preview(flow)
    if module == "numerology":
        return numerology.build_preview(flow)
    if module == "compat":
        return compatibility.build_preview(flow)
    return ""


async def show_preview(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    flow = context.user_data.get("flow", {})
    preview = build_preview(flow)
    stars, _ = pay.estimate_price(flow.get("module", "horoscope"), len(preview))
    flow["preview_text"] = preview
    flow["estimated_stars"] = stars
    context.user_data["flow"] = flow
    buttons = [
        [InlineKeyboardButton("🚀 Получить результат", callback_data="action:run")],
        [InlineKeyboardButton("🏠 Меню", callback_data="nav:home")],
    ]
    await update.effective_message.reply_text(
        f"Предпросмотр:\n{preview}\n\nОценка цены: {stars} ⭐", reply_markup=InlineKeyboardMarkup(buttons)
    )
    return STATE_PREVIEW


async def handle_run(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query:
        await query.answer()
    user_row = db.get_user(update.effective_user.id)
    flow = context.user_data.get("flow", {})
    if not pay.consume_access(user_row):
        buttons = [
            [InlineKeyboardButton(f"Купить разово ({flow.get('estimated_stars', 2)} ⭐)", callback_data="pay:once")],
            [InlineKeyboardButton("Подписка 30 дней", callback_data="pay:sub")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="nav:home")],
        ]
        await query.edit_message_text(texts.PAYWALL_TEXT, reply_markup=InlineKeyboardMarkup(buttons))
        return STATE_PAYWALL
    return await run_ai_and_show(update, context)


async def handle_pay(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer("Доступ выдан")
    flow = context.user_data.get("flow", {})
    if query.data == "pay:once":
        pay.add_credit(update.effective_user.id, 1)
    else:
        pay.grant_subscription_month(update.effective_user.id)
    return await run_ai_and_show(update, context)


def fake_ai_result(flow: Dict) -> str:
    module = flow.get("module")
    subtype = flow.get("subtype")
    preview = flow.get("preview_text", "")
    header = f"Результат {module}/{subtype}"
    bullets = "\n".join([f"• Инсайт {i}" for i in range(1, 4)])
    steps = "\n".join([f"{i}. Маленький шаг" for i in range(1, 4)])
    return f"{header}\n{preview}\n\nКлючевые тезисы:\n{bullets}\n\nЧто сделать сегодня:\n{steps}\nДисклеймер: не является предсказанием."


async def run_ai_and_show(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    flow = context.user_data.get("flow", {})
    preview = flow.get("preview_text", "")
    result_text = fake_ai_result(flow)
    tokens_in = len(preview) // 4
    tokens_out = len(result_text) // 4
    history_id = db.save_history(
        tg_id=update.effective_user.id,
        module=flow.get("module", ""),
        subtype=flow.get("subtype", ""),
        inputs=flow.get("inputs", {}),
        result_text=result_text,
        price_stars=flow.get("estimated_stars", 0),
        tokens_in=tokens_in,
        tokens_out=tokens_out,
    )
    flow["last_result_id"] = history_id
    context.user_data["flow"] = flow
    buttons = [
        [InlineKeyboardButton("🔁 Ещё раз", callback_data="nav:home")],
        [InlineKeyboardButton("⭐ В избранное", callback_data=f"fav:{history_id}")],
        [InlineKeyboardButton("🏠 Меню", callback_data="nav:home")],
    ]
    await update.effective_message.reply_text(result_text, reply_markup=InlineKeyboardMarkup(buttons))
    return STATE_RESULT


async def handle_misc_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    action = query.data
    if action == "menu:profile":
        profile_handler.render_profile(update, context)
    elif action == "menu:help":
        await query.edit_message_text(texts.HELP_TEXT, reply_markup=keyboards.BACK_MENU)
    elif action == "menu:about":
        await query.edit_message_text(texts.ABOUT_TEXT, reply_markup=keyboards.BACK_MENU)
    elif action == "menu:settings":
        await query.edit_message_text(texts.SETTINGS_TEXT, reply_markup=keyboards.BACK_MENU)
    elif action == "menu:bonus":
        await query.edit_message_text(texts.BONUS_TEXT, reply_markup=keyboards.BACK_MENU)
    elif action == "menu:premium":
        await query.edit_message_text(texts.PREMIUM_TEXT, reply_markup=keyboards.BACK_MENU)
    elif action.startswith("fav:"):
        _, hid = action.split(":", 1)
        db.toggle_favorite(int(hid), True)
        await query.answer("Сохранено в избранное")
    return ConversationHandler.END


async def handle_nav(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await back_to_menu(update, context)


async def handle_profile_actions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data == "profile:reset":
        db.reset_profile(update.effective_user.id)
        await query.edit_message_text("Профиль очищен", reply_markup=keyboards.BACK_MENU)
    elif query.data == "profile:edit":
        db.update_profile(update.effective_user.id, {"updated": datetime.utcnow().isoformat()})
        await query.edit_message_text("Профиль обновлён (заглушка)", reply_markup=keyboards.BACK_MENU)
    return ConversationHandler.END


def build_app() -> Application:
    application = Application.builder().token(config.TELEGRAM_TOKEN).concurrent_updates(True).build()

    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_module, pattern=r"^module:")],
        states={
            STATE_SELECT: [CallbackQueryHandler(handle_subtype, pattern=r"^sub:")],
            STATE_INPUT1: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_input1)],
            STATE_INPUT2: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, collect_input2),
                CallbackQueryHandler(skip_input2, pattern=r"^skip:input2"),
            ],
            STATE_PREVIEW: [CallbackQueryHandler(handle_run, pattern=r"^action:run")],
            STATE_PAYWALL: [CallbackQueryHandler(handle_pay, pattern=r"^pay:")],
            STATE_RESULT: [CallbackQueryHandler(handle_nav, pattern=r"^nav:home")],
        },
        fallbacks=[CallbackQueryHandler(handle_nav, pattern=r"^nav:home")],
        allow_reentry=True,
    )

    application.add_handler(conv)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_misc_menu, pattern=r"^menu:|^fav:"))
    application.add_handler(CallbackQueryHandler(handle_nav, pattern=r"^nav:home"))
    application.add_handler(CallbackQueryHandler(handle_profile_actions, pattern=r"^profile:"))
    application.add_handler(CallbackQueryHandler(handle_module, pattern=r"^module:"))

    return application


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    db.init_db()
    app = build_app()
    logger.info("Starting bot")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
