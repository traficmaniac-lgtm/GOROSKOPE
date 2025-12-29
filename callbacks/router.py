from __future__ import annotations

from telegram import Update
from telegram.ext import CallbackQueryHandler, ContextTypes

from app import profile_flow, storage
from services.users import profile as user_profile
from ui.menus import main_menu, paywall


async def _handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str) -> None:
    if action == "profile":
        await main_menu.render_profile(update)
    elif action == "profile:edit":
        await profile_flow.start_profile(update, context)
    elif action == "profile:reset":
        storage.reset_profile(update.effective_user.id)
        await main_menu.respond_placeholder(update, "Профиль очищен")
    elif action == "horoscope":
        await main_menu.render_horoscope_menu(update)
    elif action == "tarot":
        await main_menu.render_tarot_menu(update)
    elif action == "numerology":
        await main_menu.render_numerology_menu(update)
    elif action == "compat":
        await main_menu.render_compat_menu(update)
    elif action == "premium":
        await main_menu.render_premium(update)
    elif action == "bonus":
        await main_menu.render_bonuses(update)
    elif action == "fav":
        await main_menu.render_favorites(update)
    elif action == "settings":
        await main_menu.render_settings(update)
    elif action == "help":
        await main_menu.render_help(update)
    elif action == "about":
        await main_menu.render_about(update)
    else:
        await main_menu.respond_placeholder(update, "Скоро ✨")


async def _handle_nav(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str) -> None:
    user = user_profile.ensure_user(update.effective_user.id)
    is_new = user_profile.is_first_time(user)
    if action == "home":
        await main_menu.render_main_menu(update, context, is_new)
        user_profile.mark_returning(update.effective_user.id)
        return
    if action in {"back", "menu"}:
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
    elif data.startswith("go:profile"):
        await main_menu.render_profile(update)
    elif data.startswith("go:horoscope"):
        await main_menu.respond_placeholder(update, "Запуск гороскопа...")
    elif data.startswith("horoscope:"):
        await main_menu.respond_placeholder(update, "Короткий прогноз уже в работе ✨")
    elif data.startswith("tarot:"):
        await main_menu.respond_placeholder(update, "Карты скоро будут разложены")
    elif data.startswith("num:"):
        await main_menu.respond_placeholder(update, "Считаю цифры")
    elif data.startswith("compat:"):
        await main_menu.respond_placeholder(update, "Запроси 2 даты — расчёт готовится")
    elif data.startswith("nav:" ):
        await _handle_nav(update, context, data.split(":", maxsplit=1)[1])
    elif data in {"bonus:open", "fav:open", "help:open", "settings:open", "about:open"}:
        await main_menu.respond_placeholder(update, "Скоро ✨")
    else:
        await main_menu.respond_placeholder(update, "Скоро ✨")


def build_handlers() -> list[CallbackQueryHandler]:
    return [CallbackQueryHandler(route_callback, pattern=r"^[a-z]+:")]
