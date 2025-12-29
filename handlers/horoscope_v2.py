from __future__ import annotations

import logging
from typing import Dict, Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, ConversationHandler, ContextTypes, MessageHandler, filters

import config
from app import profile_flow, storage as profile_storage
from services import ai_service, storage as sql_storage
from ui.menus import main_menu

logger = logging.getLogger(__name__)


SELECT_FORMAT, PERSONAL_FOCUS, PERSONAL_QUESTION, CONFIRM, STYLE, PAYWALL = range(6)

FORMAT_LABELS = {
    "today": "🌞 Сегодня",
    "tomorrow": "🌙 Завтра",
    "week": "📅 Неделя",
    "month": "🧭 Месяц",
    "personal": "🌌 Персональный",
}

BASE_COST = {"today": 1, "tomorrow": 1, "week": 2, "month": 2, "personal": 3}
ZODIAC_MAP = {
    "овен": "aries",
    "телец": "taurus",
    "близнецы": "gemini",
    "рак": "cancer",
    "лев": "leo",
    "дева": "virgo",
    "весы": "libra",
    "скорпион": "scorpio",
    "стрелец": "sagittarius",
    "козерог": "capricorn",
    "водолей": "aquarius",
    "рыбы": "pisces",
}


def _reset_flow(context: ContextTypes.DEFAULT_TYPE) -> Dict:
    context.user_data.pop("horoscope_flow", None)
    return context.user_data.setdefault(
        "horoscope_flow",
        {
            "tone": "soft",
            "length": "short",
            "format": None,
            "focus": None,
            "question": None,
        },
    )


def _flow(context: ContextTypes.DEFAULT_TYPE) -> Dict:
    return context.user_data.setdefault("horoscope_flow", {})


def _nav_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("↩️ Назад", callback_data="nav:back")],
            [InlineKeyboardButton("🏠 Меню", callback_data="nav:menu")],
        ]
    )


def _format_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton("🌞 Сегодня", callback_data="hz:today")],
        [InlineKeyboardButton("🌙 Завтра", callback_data="hz:tomorrow")],
        [InlineKeyboardButton("📅 Неделя", callback_data="hz:week")],
        [InlineKeyboardButton("🧭 Месяц", callback_data="hz:month")],
        [InlineKeyboardButton("🌌 Персональный (⭐)", callback_data="hz:personal")],
        [InlineKeyboardButton("↩️ Назад", callback_data="nav:back")],
        [InlineKeyboardButton("🏠 Меню", callback_data="nav:menu")],
    ]
    return InlineKeyboardMarkup(rows)


def _focus_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton("💞 Любовь", callback_data="hzp:love")],
        [InlineKeyboardButton("💼 Работа/деньги", callback_data="hzp:money")],
        [InlineKeyboardButton("🧠 Саморазвитие", callback_data="hzp:growth")],
        [InlineKeyboardButton("🧘 Здоровье", callback_data="hzp:health")],
        [InlineKeyboardButton("🌍 Общее", callback_data="hzp:general")],
        [InlineKeyboardButton("↩️ Назад", callback_data="nav:back")],
        [InlineKeyboardButton("🏠 Меню", callback_data="nav:menu")],
    ]
    return InlineKeyboardMarkup(rows)


def _style_keyboard(flow: Dict) -> InlineKeyboardMarkup:
    tone = flow.get("tone", "soft")
    length = flow.get("length", "short")

    def mark(current: str, target: str, title: str) -> str:
        return f"{title}{' ✅' if current == target else ''}"

    rows = [
        [InlineKeyboardButton(mark(tone, "soft", "🎭 Тон: Мягко"), callback_data="st:tone:soft")],
        [InlineKeyboardButton(mark(tone, "strict", "🎭 Тон: Строго"), callback_data="st:tone:strict")],
        [InlineKeyboardButton(mark(tone, "fun", "🎭 Тон: С юмором"), callback_data="st:tone:fun")],
        [InlineKeyboardButton(mark(length, "short", "📏 Длина: Коротко"), callback_data="st:len:short")],
        [InlineKeyboardButton(mark(length, "long", "📏 Длина: Подробно"), callback_data="st:len:long")],
        [InlineKeyboardButton("✅ Готово", callback_data="nav:back_to_confirm")],
        [InlineKeyboardButton("🏠 Меню", callback_data="nav:menu")],
    ]
    return InlineKeyboardMarkup(rows)


def _confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("✅ Получить прогноз", callback_data="hz:run")],
            [InlineKeyboardButton("⚙️ Стиль ответа", callback_data="hz:style")],
            [InlineKeyboardButton("↩️ Назад", callback_data="nav:back")],
            [InlineKeyboardButton("🏠 Меню", callback_data="nav:menu")],
        ]
    )


def _result_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("⭐ В избранное", callback_data="fav:add")],
            [InlineKeyboardButton("🔄 Другой формат", callback_data="go:horoscope")],
            [InlineKeyboardButton("🧑‍💼 Профиль", callback_data="go:profile")],
            [InlineKeyboardButton("🏠 Меню", callback_data="nav:menu")],
        ]
    )


def _paywall_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("⭐ Оплатить запрос", callback_data="pay:stars:one")],
            [InlineKeyboardButton("🌟 Подписка", callback_data="pay:sub")],
            [InlineKeyboardButton("↩️ Назад", callback_data="nav:back")],
            [InlineKeyboardButton("🏠 Меню", callback_data="nav:menu")],
        ]
    )


async def _render_profile_needed(update: Update) -> None:
    if update.effective_message:
        await update.effective_message.edit_text(
            "Для гороскопа нужен профиль (дата рождения или знак).",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("✨ Заполнить профиль", callback_data="pf:wizard")],
                    [InlineKeyboardButton("↩️ Назад", callback_data="nav:back")],
                    [InlineKeyboardButton("🏠 Меню", callback_data="nav:menu")],
                ]
            ),
        )


def _has_profile(user_id: int) -> bool:
    user = profile_storage.get_user(user_id)
    profile = profile_storage.Profile.from_dict(user.get("profile"))
    return bool(profile.birth_date or profile.sign)


def _map_zodiac(profile: profile_storage.Profile) -> Optional[str]:
    sign = (profile.sign or "").strip().lower()
    mapped = ZODIAC_MAP.get(sign)
    if mapped:
        return mapped
    if profile.birth_date:
        auto = profile_flow.zodiac_from_date(profile.birth_date).lower()
        return ZODIAC_MAP.get(auto)
    return None


async def open_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    _reset_flow(context)
    if update.callback_query:
        await update.callback_query.answer()
        if update.effective_message:
            await update.effective_message.edit_text(
                "🔮 Выбери формат прогноза:", reply_markup=_format_keyboard()
            )
    elif update.effective_message:
        await update.effective_message.reply_text(
            "🔮 Выбери формат прогноза:", reply_markup=_format_keyboard()
        )
    return SELECT_FORMAT


async def select_format(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    assert query
    await query.answer()
    flow = _flow(context)
    flow["format"] = query.data.split(":", maxsplit=1)[1]
    if not _has_profile(update.effective_user.id):
        await _render_profile_needed(update)
        return SELECT_FORMAT
    if flow["format"] == "personal":
        if update.effective_message:
            await update.effective_message.edit_text(
                "🌌 Персональный прогноз: выбери фокус",
                reply_markup=_focus_keyboard(),
            )
        return PERSONAL_FOCUS
    return await render_confirm(update, context)


async def select_focus(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    assert query
    await query.answer()
    flow = _flow(context)
    flow["focus"] = query.data.split(":", maxsplit=1)[1]
    if update.effective_message:
        await update.effective_message.edit_text(
            "Напиши 1 вопрос (необязательно). Если без вопроса — сделаю общий персональный прогноз.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("Без вопроса", callback_data="hzp:qskip")],
                    [InlineKeyboardButton("↩️ Назад", callback_data="nav:back")],
                    [InlineKeyboardButton("🏠 Меню", callback_data="nav:menu")],
                ]
            ),
        )
    return PERSONAL_QUESTION


async def set_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = (update.effective_message.text or "").strip()
    flow = _flow(context)
    flow["question"] = text or None
    return await render_confirm(update, context)


async def skip_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query:
        await update.callback_query.answer()
    flow = _flow(context)
    flow["question"] = None
    return await render_confirm(update, context)


def _build_cost_info(flow: Dict, user_row: Dict) -> tuple[int, int, bool]:
    free_left = int(user_row.get("free_remaining", 0))
    subscription = sql_storage.subscription_active(user_row)
    stars_price = 3
    if subscription:
        return 0, stars_price, subscription
    if flow.get("format") != "personal" and free_left > 0:
        return 0, stars_price, subscription
    return stars_price, stars_price, subscription


async def render_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    flow = _flow(context)
    user_row = sql_storage.get_user(update.effective_user.id)
    cost, stars_price, subscription = _build_cost_info(flow, user_row)
    free_left = int(user_row.get("free_remaining", 0))
    tone = flow.get("tone", "soft")
    length = flow.get("length", "short")
    summary = [
        "✅ Подтверди запрос",
        f"Формат: {FORMAT_LABELS.get(flow.get('format', ''), flow.get('format', ''))}",
        f"Осталось бесплатных: {free_left}",
        f"Стоимость: {cost}⭐" if cost else "Стоимость: 0",
        f"Тон/длина из настроек: {tone}/{length}",
    ]
    if flow.get("format") == "personal" and flow.get("focus"):
        summary.append(f"Фокус: {flow['focus']}")
    if flow.get("question"):
        summary.append(f"Вопрос: {flow['question']}")

    flow["pending_cost"] = cost
    flow["stars_price"] = stars_price
    flow["free_left"] = free_left
    flow["subscription"] = subscription

    if update.callback_query:
        await update.callback_query.answer()
    if update.effective_message:
        await update.effective_message.edit_text("\n".join(summary), reply_markup=_confirm_keyboard())
    return CONFIRM


def _build_payload(flow: Dict, profile: profile_storage.Profile) -> Dict:
    zodiac = _map_zodiac(profile) or ""
    tone = flow.get("tone", "soft")
    length = flow.get("length", "short")
    if flow.get("format") == "personal":
        return {
            "format": "personal",
            "zodiac": zodiac,
            "focus": flow.get("focus"),
            "question": flow.get("question"),
            "locale": "ru",
            "tone": tone,
            "length": length,
        }
    return {
        "format": flow.get("format"),
        "zodiac": zodiac,
        "locale": "ru",
        "tone": tone,
        "length": length,
    }


async def _render_paywall(update: Update, price: int) -> int:
    if update.effective_message:
        await update.effective_message.edit_text(
            f"Лимит бесплатных запросов исчерпан\nСтоимость: {price}⭐",
            reply_markup=_paywall_keyboard(),
        )
    return PAYWALL


async def run_forecast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    flow = _flow(context)
    if update.callback_query:
        await update.callback_query.answer()
    user_id = update.effective_user.id
    user_row = sql_storage.get_user(user_id)
    cost, stars_price, subscription = _build_cost_info(flow, user_row)
    flow["pending_cost"] = cost
    flow["stars_price"] = stars_price
    flow["free_left"] = int(user_row.get("free_remaining", 0))
    flow["subscription"] = subscription
    prepaid = bool(flow.pop("prepaid", False))
    prepaid_amount = int(flow.pop("prepaid_amount", cost if prepaid else 0))

    if prepaid:
        cost = prepaid_amount

    if not _has_profile(user_id):
        await _render_profile_needed(update)
        return SELECT_FORMAT

    if not subscription and flow["free_left"] == 0 and cost and not prepaid:
        return await _render_paywall(update, cost)

    if cost and not subscription and not prepaid:
        if int(user_row.get("stars_balance", 0)) < cost:
            return await _render_paywall(update, cost)
        sql_storage.adjust_balance(user_id, stars_delta=-cost)

    profile = profile_storage.Profile.from_dict(profile_storage.get_user(user_id).get("profile"))
    payload = _build_payload(flow, profile)

    if update.effective_message:
        await update.effective_message.edit_text("⏳ Готовлю прогноз...")

    result = ai_service.run_ai_task(user_id, "horoscope", payload)
    tokens = (result.get("tokens_in", 0), result.get("tokens_out", 0))
    latency = result.get("latency", 0.0)

    if cost == 0 and not subscription and flow.get("format") != "personal" and flow.get("free_left", 0) > 0:
        sql_storage.adjust_balance(user_id, free_delta=-1)

    history_id = sql_storage.save_history(
        user_id=user_id,
        mode="horoscope",
        subtype=flow.get("format", ""),
        payload=payload,
        answer=result.get("answer", ""),
        tokens=tokens,
        price_stars=cost,
    )
    flow["last_history_id"] = history_id

    footer = f"\n— GOROSKOPE • tokens: {tokens[0] + tokens[1]} • cost: {cost} ⭐"
    if update.effective_message:
        await update.effective_message.edit_text(
            (result.get("answer", "") or "") + footer,
            reply_markup=_result_keyboard(),
        )
    logger.info(
        "Horoscope generated",
        extra={"user_id": user_id, "cost": cost, "tokens": tokens, "latency": latency},
    )
    return ConversationHandler.END


async def pay_with_stars(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    flow = _flow(context)
    price = int(flow.get("pending_cost") or flow.get("stars_price") or 0)
    if update.callback_query:
        await update.callback_query.answer()
    user_row = sql_storage.get_user(update.effective_user.id)
    balance = int(user_row.get("stars_balance", 0))
    if balance < price:
        if update.effective_message:
            await update.effective_message.edit_text(
                "Недостаточно звёзд. Попробуй подписку или пополнение.",
                reply_markup=_paywall_keyboard(),
            )
        return PAYWALL

    sql_storage.adjust_balance(update.effective_user.id, stars_delta=-price)
    flow["prepaid"] = True
    flow["prepaid_amount"] = price
    return await run_forecast(update, context)


async def pay_with_sub(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query:
        await update.callback_query.answer()
    until = int(sql_storage.get_user(update.effective_user.id).get("subscription_until", 0))
    sql_storage.set_subscription(update.effective_user.id, until + int(config.SUBSCRIPTION_DELTA.total_seconds()))
    return await run_forecast(update, context)


async def open_style(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    flow = _flow(context)
    if update.callback_query:
        await update.callback_query.answer()
    if update.effective_message:
        await update.effective_message.edit_text("⚙️ Стиль ответа", reply_markup=_style_keyboard(flow))
    return STYLE


async def set_tone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    assert query
    await query.answer()
    tone = query.data.split(":")[-1]
    _flow(context)["tone"] = tone
    if update.effective_message:
        await update.effective_message.edit_reply_markup(reply_markup=_style_keyboard(_flow(context)))
    return STYLE


async def set_length(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    assert query
    await query.answer()
    length = query.data.split(":")[-1]
    _flow(context)["length"] = length
    if update.effective_message:
        await update.effective_message.edit_reply_markup(reply_markup=_style_keyboard(_flow(context)))
    return STYLE


async def back_to_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query:
        await update.callback_query.answer()
    return await render_confirm(update, context)


async def handle_back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    flow = _flow(context)
    current_format = flow.get("format")
    if update.callback_query:
        await update.callback_query.answer()
    if current_format == "personal" and context.user_data.get("horoscope_flow", {}).get("focus"):
        if update.effective_message:
            await update.effective_message.edit_text(
                "🌌 Персональный прогноз: выбери фокус", reply_markup=_focus_keyboard()
            )
        return PERSONAL_FOCUS
    return await open_menu(update, context)


async def add_favorite(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query:
        await update.callback_query.answer(text="Сохранено в избранное ✨")
    history_id = _flow(context).get("last_history_id")
    if history_id:
        sql_storage.mark_favorite(int(history_id), True)
    return ConversationHandler.END


async def go_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query:
        await update.callback_query.answer()
    await main_menu.render_profile(update)
    return ConversationHandler.END


async def go_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = profile_storage.get_user(update.effective_user.id)
    await main_menu.render_main_menu(update, context, is_new_user=user.get("is_new", False))
    return ConversationHandler.END


def build_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(open_menu, pattern=r"^go:horoscope$")],
        states={
            SELECT_FORMAT: [
                CallbackQueryHandler(select_format, pattern=r"^hz:(today|tomorrow|week|month|personal)$"),
                CallbackQueryHandler(go_menu, pattern=r"^nav:menu$"),
                CallbackQueryHandler(handle_back, pattern=r"^nav:back$"),
            ],
            PERSONAL_FOCUS: [CallbackQueryHandler(select_focus, pattern=r"^hzp:(love|money|growth|health|general)$"), CallbackQueryHandler(handle_back, pattern=r"^nav:back$")],
            PERSONAL_QUESTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, set_question),
                CallbackQueryHandler(skip_question, pattern=r"^hzp:qskip$"),
                CallbackQueryHandler(handle_back, pattern=r"^nav:back$"),
                CallbackQueryHandler(go_menu, pattern=r"^nav:menu$"),
            ],
            CONFIRM: [
                CallbackQueryHandler(run_forecast, pattern=r"^hz:run$"),
                CallbackQueryHandler(open_style, pattern=r"^hz:style$"),
                CallbackQueryHandler(handle_back, pattern=r"^nav:back$"),
                CallbackQueryHandler(go_menu, pattern=r"^nav:menu$"),
            ],
            STYLE: [
                CallbackQueryHandler(set_tone, pattern=r"^st:tone:"),
                CallbackQueryHandler(set_length, pattern=r"^st:len:"),
                CallbackQueryHandler(back_to_confirm, pattern=r"^nav:back_to_confirm$"),
                CallbackQueryHandler(go_menu, pattern=r"^nav:menu$"),
            ],
            PAYWALL: [
                CallbackQueryHandler(pay_with_stars, pattern=r"^pay:stars:one$"),
                CallbackQueryHandler(pay_with_sub, pattern=r"^pay:sub$"),
                CallbackQueryHandler(handle_back, pattern=r"^nav:back$"),
                CallbackQueryHandler(go_menu, pattern=r"^nav:menu$"),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(open_menu, pattern=r"^go:horoscope$"),
            CallbackQueryHandler(go_menu, pattern=r"^nav:menu$"),
            CallbackQueryHandler(go_profile, pattern=r"^go:profile$"),
            CallbackQueryHandler(add_favorite, pattern=r"^fav:add$"),
        ],
        allow_reentry=True,
    )

