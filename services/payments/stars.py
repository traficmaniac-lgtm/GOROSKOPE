from __future__ import annotations

import time
from typing import Dict

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice, Update
from telegram.ext import ContextTypes

from app import storage

PLANS: Dict[str, Dict[str, object]] = {
    "day": {"amount": 25, "title": "1 день", "duration_days": 1},
    "week": {"amount": 99, "title": "7 дней", "duration_days": 7},
    "month": {"amount": 299, "title": "30 дней", "duration_days": 30},
    "life": {"amount": 999, "title": "Навсегда", "duration_days": None},
}


def _build_payload(plan: str, user_id: int) -> str:
    timestamp = int(time.time())
    return f"GORO_PREMIUM|{plan}|{user_id}|{timestamp}"


def _build_prices(plan: str) -> list[LabeledPrice]:
    info = PLANS[plan]
    label = f"⭐️ {info['title']}"
    return [LabeledPrice(label=label, amount=int(info["amount"]))]


def has_active_premium(user_id: int) -> bool:
    user = storage.get_user(user_id)
    return storage.has_premium(user)


async def send_plan_invoice(update: Update, context: ContextTypes.DEFAULT_TYPE, plan: str) -> None:
    if plan not in PLANS:
        if update.callback_query:
            await update.callback_query.answer(text="План недоступен", show_alert=True)
        return

    chat_id = update.effective_chat.id if update.effective_chat else None
    if chat_id is None:
        return

    payload = _build_payload(plan, update.effective_user.id)
    prices = _build_prices(plan)

    await context.bot.send_invoice(
        chat_id=chat_id,
        title="⭐️ Премиум доступ",
        description="Открой точные расклады и совместимость",
        payload=payload,
        provider_token="",
        currency="XTR",
        prices=prices,
        max_tip_amount=0,
    )


async def handle_precheckout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.pre_checkout_query
    if query:
        await query.answer(ok=True)


def _set_premium(user_id: int, plan: str, telegram_charge_id: str | None, provider_charge_id: str | None) -> None:
    now = int(time.time())
    data = storage.get_user(user_id)
    plan_info = PLANS.get(plan, {})
    duration = plan_info.get("duration_days")

    if duration:
        until = now + int(duration) * 86400
        data["premium_until"] = until
    else:
        data["premium_until"] = 0
    data["premium_lifetime"] = duration is None
    data["is_premium"] = True
    data["last_payment_charge_id"] = provider_charge_id or ""
    data["telegram_payment_charge_id"] = telegram_charge_id or ""

    storage.save_user(user_id, data)


async def handle_successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if not message or not message.successful_payment:
        return

    payment = message.successful_payment
    payload = payment.invoice_payload or ""
    parts = payload.split("|")
    plan = parts[1] if len(parts) >= 2 else "day"

    _set_premium(
        user_id=update.effective_user.id,
        plan=plan,
        telegram_charge_id=payment.telegram_payment_charge_id,
        provider_charge_id=payment.provider_payment_charge_id,
    )

    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🔮 Гороскоп", callback_data="menu:horoscope")],
            [InlineKeyboardButton("🏠 Меню", callback_data="nav:home")],
        ]
    )
    await message.reply_text("✅ Доступ активирован", reply_markup=keyboard)


async def restore_if_possible(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if has_active_premium(user_id):
        return

    message = update.effective_message
    if message:
        await message.reply_text(
            "Покупка не найдена. Оплати любой план заново.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("⭐️ Открыть планы", callback_data="paywall:open")]]
            ),
        )
