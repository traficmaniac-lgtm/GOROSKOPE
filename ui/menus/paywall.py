from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from services.payments import stars
from ui.menus import main_menu

PAYWALL_TITLE = "⭐️ Премиум: открой точные расчёты"


def build_paywall_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("⭐️ 1 день — 25 XTR", callback_data="pay:plan:day"),
                InlineKeyboardButton("⭐️ 7 дней — 99 XTR", callback_data="pay:plan:week"),
            ],
            [
                InlineKeyboardButton("⭐️ 30 дней — 299 XTR", callback_data="pay:plan:month"),
                InlineKeyboardButton("⭐️ Навсегда — 999 XTR", callback_data="pay:plan:life"),
            ],
            [
                InlineKeyboardButton("🧾 Что входит?", callback_data="paywall:features"),
                InlineKeyboardButton("🔄 Восстановить покупку", callback_data="paywall:restore"),
            ],
            [
                InlineKeyboardButton("⬅️ Назад", callback_data="nav:back"),
                InlineKeyboardButton("🏠 Меню", callback_data="nav:home"),
            ],
        ]
    )


async def render_paywall(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = build_paywall_keyboard()
    message = update.effective_message
    if update.callback_query:
        await update.callback_query.answer()
        if message:
            try:
                await message.edit_text(PAYWALL_TITLE, reply_markup=keyboard)
            except Exception:  # noqa: BLE001
                await message.edit_reply_markup(reply_markup=keyboard)
    elif message:
        await message.reply_text(PAYWALL_TITLE, reply_markup=keyboard)


async def handle_pay_plan(update: Update, context: ContextTypes.DEFAULT_TYPE, plan: str) -> None:
    if update.callback_query:
        await update.callback_query.answer()
    await stars.send_plan_invoice(update, context, plan)


async def show_features(update: Update) -> None:
    if update.callback_query:
        await update.callback_query.answer(
            text="Полный доступ: точные расклады, совместимость, расклад дня.", show_alert=True
        )


async def restore_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if update.callback_query:
        await update.callback_query.answer()
    if stars.has_active_premium(user_id):
        await main_menu.respond_placeholder(update, "Уже активен ⭐️")
        return
    await stars.restore_if_possible(update, context)
