from __future__ import annotations

import hashlib
import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.core import texts
from app.core.keyboards import (
    focus_kb,
    gender_kb,
    horoscope_menu_kb,
    limit_kb,
    main_menu_kb,
    result_kb,
    time_known_kb,
)
from app.core.states import HoroscopeStates
from app.core.validators import validate_date, validate_time
from app.services.ai_service import AIService
from app.services.payment_service import PaymentService
from app.services.prompt_builder import HoroscopeRequest, build_horoscope_prompt
from app.services.quota_service import QuotaService

logger = logging.getLogger(__name__)

horoscope_router = Router()

quota_service: QuotaService | None = None
ai_service: AIService | None = None
payment_service: PaymentService | None = None


def init_horoscope_services(qs: QuotaService, ai: AIService, pay: PaymentService) -> None:
    global quota_service, ai_service, payment_service
    quota_service = qs
    ai_service = ai
    payment_service = pay


def _ensure_services() -> None:
    if not quota_service or not ai_service or not payment_service:
        raise RuntimeError("Services are not initialized")


@horoscope_router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(texts.WELCOME, reply_markup=main_menu_kb())


@horoscope_router.callback_query(F.data == "back_main")
async def back_to_main(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await call.message.edit_text(texts.WELCOME, reply_markup=main_menu_kb())
    await call.answer()


@horoscope_router.callback_query(F.data == "menu_about")
async def about(call: CallbackQuery) -> None:
    await call.message.edit_text(texts.ABOUT, reply_markup=main_menu_kb())
    await call.answer()


@horoscope_router.callback_query(F.data == "menu_settings")
async def settings(call: CallbackQuery) -> None:
    await call.message.edit_text(texts.SETTINGS, reply_markup=main_menu_kb())
    await call.answer()


@horoscope_router.callback_query(F.data == "menu_balance")
async def balance(call: CallbackQuery) -> None:
    _ensure_services()
    free_left = await quota_service.get_free_left(call.from_user.id)  # type: ignore[union-attr]
    await call.message.edit_text(texts.BALANCE.format(free_left=free_left), reply_markup=main_menu_kb())
    await call.answer()


@horoscope_router.callback_query(F.data == "menu_horoscope")
async def open_horoscope(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await call.message.edit_text("Выберите тип гороскопа", reply_markup=horoscope_menu_kb())
    await call.answer()


@horoscope_router.callback_query(F.data.in_({"hs_today", "hs_week"}))
async def start_horoscope(call: CallbackQuery, state: FSMContext) -> None:
    mode = "Прогноз на сегодня" if call.data == "hs_today" else "Прогноз на неделю"
    await state.update_data(mode=mode, action=call.data)
    await state.set_state(HoroscopeStates.waiting_for_birth_date)
    await call.message.edit_text(texts.ASK_BIRTH_DATE)
    await call.answer()


@horoscope_router.callback_query(F.data == "hs_natal")
async def natal_soon(call: CallbackQuery) -> None:
    await call.message.edit_text(texts.NATAL_SOON, reply_markup=horoscope_menu_kb())
    await call.answer()


@horoscope_router.callback_query(F.data == "back_horoscope")
async def back_horoscope(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await call.message.edit_text("Выберите тип гороскопа", reply_markup=horoscope_menu_kb())
    await call.answer()


@horoscope_router.message(HoroscopeStates.waiting_for_birth_date)
async def birth_date(message: Message, state: FSMContext) -> None:
    if not validate_date(message.text or ""):
        await message.answer(texts.INVALID_DATE)
        return
    await state.update_data(birth_date=message.text)
    await state.set_state(HoroscopeStates.waiting_for_time_known)
    await message.answer(texts.ASK_TIME_KNOWN, reply_markup=time_known_kb())


@horoscope_router.callback_query(HoroscopeStates.waiting_for_time_known, F.data.in_({"time_yes", "time_no"}))
async def time_known(call: CallbackQuery, state: FSMContext) -> None:
    if call.data == "time_yes":
        await state.set_state(HoroscopeStates.waiting_for_birth_time)
        await call.message.edit_text(texts.ASK_BIRTH_TIME)
    else:
        await state.update_data(birth_time=None)
        await state.set_state(HoroscopeStates.waiting_for_birth_place)
        await call.message.edit_text(texts.ASK_BIRTH_PLACE)
    await call.answer()


@horoscope_router.message(HoroscopeStates.waiting_for_birth_time)
async def birth_time(message: Message, state: FSMContext) -> None:
    if not validate_time(message.text or ""):
        await message.answer(texts.INVALID_TIME)
        return
    await state.update_data(birth_time=message.text)
    await state.set_state(HoroscopeStates.waiting_for_birth_place)
    await message.answer(texts.ASK_BIRTH_PLACE)


@horoscope_router.message(HoroscopeStates.waiting_for_birth_place)
async def birth_place(message: Message, state: FSMContext) -> None:
    await state.update_data(birth_place=message.text)
    await state.set_state(HoroscopeStates.waiting_for_gender)
    await message.answer(texts.ASK_GENDER, reply_markup=gender_kb())


@horoscope_router.callback_query(HoroscopeStates.waiting_for_gender, F.data.startswith("gender_"))
async def gender(call: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(gender=call.data)
    await state.set_state(HoroscopeStates.waiting_for_focus)
    await call.message.edit_text(texts.ASK_FOCUS, reply_markup=focus_kb())
    await call.answer()


@horoscope_router.callback_query(HoroscopeStates.waiting_for_focus, F.data.startswith("focus_"))
async def focus(call: CallbackQuery, state: FSMContext) -> None:
    _ensure_services()
    await state.update_data(focus=call.data)
    data = await state.get_data()

    free_left = await quota_service.get_free_left(call.from_user.id)  # type: ignore[union-attr]
    if free_left <= 0:
        await state.clear()
        await call.message.edit_text(texts.LIMIT_REACHED, reply_markup=limit_kb())
        await call.answer()
        return

    consumed = await quota_service.consume_one(call.from_user.id)  # type: ignore[union-attr]
    if not consumed:
        await state.clear()
        await call.message.edit_text(texts.LIMIT_REACHED, reply_markup=limit_kb())
        await call.answer()
        return

    req = HoroscopeRequest(
        mode=data.get("mode", "Гороскоп"),
        birth_date=data.get("birth_date", ""),
        birth_time=data.get("birth_time"),
        birth_place=data.get("birth_place", ""),
        gender=data.get("gender", ""),
        focus=data.get("focus", call.data),
    )
    prompt = build_horoscope_prompt(req)
    prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()
    await quota_service.log_request(call.from_user.id, "horoscope", data.get("action", ""), prompt_hash)  # type: ignore[union-attr]

    await call.message.edit_text(texts.PROCESSING)
    try:
        response = await ai_service.generate(prompt)  # type: ignore[union-attr]
    except Exception as exc:  # pragma: no cover - runtime guard
        logger.exception("AI generation failed: %s", exc)
        await quota_service.refund_one(call.from_user.id)  # type: ignore[union-attr]
        await call.message.edit_text(texts.GENERATION_ERROR, reply_markup=horoscope_menu_kb())
        await call.answer()
        return

    await state.update_data(last_request=req.__dict__)
    await state.set_state(HoroscopeStates.waiting_for_regeneration)
    await call.message.edit_text(response, reply_markup=result_kb())
    await call.answer()


@horoscope_router.callback_query(F.data == "regen")
async def regenerate(call: CallbackQuery, state: FSMContext) -> None:
    _ensure_services()
    data = await state.get_data()
    last_request = data.get("last_request")
    if not last_request:
        await call.message.edit_text(texts.ASK_BIRTH_DATE)
        await state.set_state(HoroscopeStates.waiting_for_birth_date)
        await call.answer()
        return

    free_left = await quota_service.get_free_left(call.from_user.id)  # type: ignore[union-attr]
    if free_left <= 0:
        await call.message.edit_text(texts.LIMIT_REACHED, reply_markup=limit_kb())
        await call.answer()
        return

    consumed = await quota_service.consume_one(call.from_user.id)  # type: ignore[union-attr]
    if not consumed:
        await call.message.edit_text(texts.LIMIT_REACHED, reply_markup=limit_kb())
        await call.answer()
        return

    req = HoroscopeRequest(**last_request)
    prompt = build_horoscope_prompt(req)
    prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()
    await quota_service.log_request(call.from_user.id, "horoscope", data.get("action", "regen"), prompt_hash)  # type: ignore[union-attr]

    await call.message.edit_text(texts.PROCESSING)
    try:
        response = await ai_service.generate(prompt)  # type: ignore[union-attr]
    except Exception as exc:  # pragma: no cover - runtime guard
        logger.exception("AI regeneration failed: %s", exc)
        await quota_service.refund_one(call.from_user.id)  # type: ignore[union-attr]
        await call.message.edit_text(texts.GENERATION_ERROR, reply_markup=horoscope_menu_kb())
        await call.answer()
        return

    await call.message.edit_text(response, reply_markup=result_kb())
    await call.answer()


@horoscope_router.callback_query(F.data.in_({"limit_buy", "limit_sub"}))
async def limit_stub(call: CallbackQuery) -> None:
    _ensure_services()
    if call.data == "limit_buy":
        msg = await payment_service.create_purchase_intent(call.from_user.id)  # type: ignore[union-attr]
    else:
        msg = await payment_service.create_subscription_intent(call.from_user.id)  # type: ignore[union-attr]
    await call.message.edit_text(msg, reply_markup=limit_kb())
    await call.answer()
