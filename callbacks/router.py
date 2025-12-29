from __future__ import annotations

from telegram import Update
from telegram.ext import CallbackQueryHandler, ContextTypes

from app import profile_flow
from services.users import profile as user_profile
from ui.menus import main_menu, paywall


async def _handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str) -> None:
    if action == "profile":
        await profile_flow.start_profile(update, context)
    elif action in {"horoscope", "tarot", "numerology", "compat"}:
        await main_menu.respond_placeholder(update, "Скоро ✨")
    else:
        await main_menu.respond_placeholder(update, "В разработке")


async def _handle_nav(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str) -> None:
    user = user_profile.ensure_user(update.effective_user.id)
    is_new = user_profile.is_first_time(user)
    if action == "home":
        await main_menu.render_main_menu(update, context, is_new)
        user_profile.mark_returning(update.effective_user.id)
        return
    if action == "back":
        await main_menu.render_main_menu(update, context, is_new)
        user_profile.mark_returning(update.effective_user.id)


async def route_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query or not query.data:
        return

    data = query.data

    if data in {"menu:profile", "onboard:fast", "action:calculate"}:
        return

    if data.startswith("menu:"):
        await _handle_menu(update, context, data.split(":", maxsplit=1)[1])
    elif data.startswith("onboard:fast"):
        await profile_flow.start_profile(update, context)
    elif data.startswith("paywall:open"):
        await paywall.render_paywall(update, context)
    elif data.startswith("paywall:features"):
        await paywall.show_features(update)
    elif data.startswith("paywall:restore"):
        await paywall.restore_purchase(update, context)
    elif data.startswith("pay:plan:"):
        plan = data.split(":", maxsplit=2)[2]
        await paywall.handle_pay_plan(update, context, plan)
    elif data.startswith("nav:" ):
        await _handle_nav(update, context, data.split(":", maxsplit=1)[1])
    elif data in {"bonus:open", "fav:open", "help:open", "settings:open", "about:open"}:
        await main_menu.respond_placeholder(update, "Скоро ✨")
    else:
        await main_menu.respond_placeholder(update, "Скоро ✨")


def build_handlers() -> list[CallbackQueryHandler]:
    return [CallbackQueryHandler(route_callback, pattern=r"^[a-z]+:")]
