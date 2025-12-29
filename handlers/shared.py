from __future__ import annotations

from typing import Any, Dict

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from services import ai_service, billing_service, storage


async def send_forecast(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    payload: Dict[str, Any],
    result_buttons: InlineKeyboardMarkup,
) -> None:
    price = billing_service.price_for_mode(payload.get("mode", ""))
    billing_service.consume(update.effective_user.id, price)
    result = ai_service.generate_forecast(payload)
    storage.save_history(
        user_id=update.effective_user.id,
        mode=payload.get("mode", ""),
        subtype=payload.get("subtype", ""),
        payload=payload,
        answer=result["answer"],
        tokens=(result["tokens_in"], result["tokens_out"]),
        price_stars=price,
    )
    await update.effective_message.reply_text(result["answer"], reply_markup=result_buttons)


async def ensure_access_or_paywall(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    payload: Dict[str, Any],
    result_buttons: InlineKeyboardMarkup,
) -> None:
    price = billing_service.price_for_mode(payload.get("mode", ""))
    user = storage.get_user(update.effective_user.id)
    if billing_service.can_access(user, price):
        await send_forecast(update, context, payload, result_buttons)
        return

    draft_id = storage.save_draft(
        update.effective_user.id, payload.get("mode", ""), payload.get("subtype", ""), payload
    )
    context.bot_data.setdefault("draft_buttons", {})[draft_id] = result_buttons
    buttons = [
        [InlineKeyboardButton(f"⭐️ Купить {price} Stars", callback_data=f"pay:stars:{draft_id}:{price}")],
        [InlineKeyboardButton("✅ Подписка на месяц", callback_data=f"pay:sub:{draft_id}")],
        [InlineKeyboardButton("↩️ Назад", callback_data="nav:home")],
    ]
    await update.effective_message.reply_text(
        "Нужна оплата: выбери Stars или подписку", reply_markup=InlineKeyboardMarkup(buttons)
    )


async def handle_payment_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    parts = query.data.split(":")
    if len(parts) < 3:
        return
    _, kind, draft_id = parts[:3]
    draft_id_int = int(draft_id)
    payload = storage.pop_draft(draft_id_int)
    buttons_map = context.bot_data.get("draft_buttons", {})
    result_buttons = buttons_map.pop(draft_id_int, InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Домой", callback_data="nav:home")]]))
    if kind == "stars":
        price = int(parts[3]) if len(parts) > 3 else billing_service.price_for_mode(payload.get("mode", ""))
        billing_service.grant_stars(update.effective_user.id, price)
    elif kind == "sub":
        billing_service.grant_subscription_days(update.effective_user.id)
    if payload:
        await send_forecast(update, context, payload, result_buttons)

