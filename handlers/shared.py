from __future__ import annotations

from typing import Any, Dict

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from services import ai_service, storage
from shared import quota


async def send_forecast(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    payload: Dict[str, Any],
    result_buttons: InlineKeyboardMarkup,
    price_stars: int,
) -> None:
    result = ai_service.generate_forecast(payload)
    storage.save_history(
        user_id=update.effective_user.id,
        mode=payload.get("mode", ""),
        subtype=payload.get("subtype", ""),
        payload=payload,
        answer=result["answer"],
        tokens=(result["tokens_in"], result["tokens_out"]),
        price_stars=price_stars,
    )
    await update.effective_message.reply_text(result["answer"], reply_markup=result_buttons)


async def ensure_access_or_paywall(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    payload: Dict[str, Any],
    result_buttons: InlineKeyboardMarkup,
) -> None:
    prompt = ai_service.build_prompt(payload)
    if quota.can_use_free(update.effective_user.id):
        remaining = quota.consume_free(update.effective_user.id)
        await send_forecast(update, context, payload, result_buttons, price_stars=0)
        return

    allowed, price = quota.ensure_payment(update.effective_user.id, len(prompt), payload.get("model", "gpt"))
    if allowed:
        await send_forecast(update, context, payload, result_buttons, price_stars=price)
        return

    draft_id = storage.save_draft(
        update.effective_user.id, payload.get("mode", ""), payload.get("subtype", ""), payload
    )
    context.bot_data.setdefault("draft_buttons", {})[draft_id] = result_buttons
    buttons = [
        [InlineKeyboardButton(f"⭐️ Оплатить звёздами ({price})", callback_data=f"pay:stars:{draft_id}:{price}")],
        [InlineKeyboardButton("💳 Подписка на месяц", callback_data=f"pay:sub:{draft_id}")],
        [InlineKeyboardButton("🏠 Домой", callback_data="nav:home")],
    ]
    await update.effective_message.reply_text(
        "Закончились бесплатные запросы. Выбери способ оплаты:", reply_markup=InlineKeyboardMarkup(buttons)
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
    result_buttons = buttons_map.pop(
        draft_id_int, InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Домой", callback_data="nav:home")]])
    )
    price = int(parts[3]) if len(parts) > 3 else 0
    if payload:
        if kind == "stars":
            allowed, _ = quota.ensure_payment(update.effective_user.id, len(ai_service.build_prompt(payload)), payload.get("model", "gpt"))
            if not allowed:
                await query.edit_message_text(
                    "Недостаточно звёзд. Пополните баланс.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Домой", callback_data="nav:home")]])
                )
                return
        elif kind == "sub":
            # подписка воспринимается как оплата
            pass
        await send_forecast(update, context, payload, result_buttons, price_stars=price)

