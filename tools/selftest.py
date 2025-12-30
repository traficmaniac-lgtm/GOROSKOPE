from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from app.core.keyboards import (
    focus_kb,
    gender_kb,
    horoscope_menu_kb,
    limit_kb,
    main_menu_kb,
    result_kb,
    time_known_kb,
)
from app.core.router import setup_routers
from app.db.storage import Database
from app.services.prompt_builder import HoroscopeRequest, build_horoscope_prompt
from app.services.quota_service import QuotaService

HANDLED_CALLBACKS: set[str] = {
    "menu_horoscope",
    "menu_balance",
    "menu_settings",
    "menu_about",
    "hs_today",
    "hs_week",
    "hs_natal",
    "back_main",
    "time_yes",
    "time_no",
    "gender_m",
    "gender_f",
    "gender_o",
    "focus_love",
    "focus_money",
    "focus_health",
    "focus_career",
    "focus_general",
    "limit_buy",
    "limit_sub",
    "back_horoscope",
    "regen",
}


@dataclass
class TestResult:
    name: str
    success: bool
    details: str = ""


def gather_keyboard_callbacks() -> set[str]:
    callbacks: set[str] = set()
    for kb in [
        main_menu_kb(),
        horoscope_menu_kb(),
        time_known_kb(),
        gender_kb(),
        focus_kb(),
        limit_kb(),
        result_kb(),
    ]:
        for row in kb.inline_keyboard:
            for button in row:
                if button.callback_data:
                    callbacks.add(str(button.callback_data))
    return callbacks


def check_router_handlers() -> None:
    router = setup_routers()
    total_handlers = sum(len(observer.handlers) for observer in router.observers.values())
    if total_handlers == 0:
        raise AssertionError("Router не содержит зарегистрированных обработчиков")
    callback_handlers = len(router.observers["callback_query"].handlers)
    if callback_handlers == 0:
        raise AssertionError("Нет обработчиков callback_query")


def check_callback_coverage() -> None:
    keyboard_callbacks = gather_keyboard_callbacks()
    missing_handlers = keyboard_callbacks - HANDLED_CALLBACKS
    unknown_listed = HANDLED_CALLBACKS - keyboard_callbacks
    if missing_handlers:
        raise AssertionError(f"Для callback отсутствуют обработчики: {sorted(missing_handlers)}")
    if unknown_listed:
        raise AssertionError(
            f"В HANDLED_CALLBACKS перечислены кнопки, которых нет в клавиатурах: {sorted(unknown_listed)}"
        )


def check_prompt_builder() -> None:
    req = HoroscopeRequest(
        mode="Тест",
        birth_date="01.01.1990",
        birth_time=None,
        birth_place="Москва",
        gender="gender_f",
        focus="focus_general",
    )
    prompt = build_horoscope_prompt(req)
    if not prompt.system_prompt or not prompt.user_prompt:
        raise AssertionError("Prompt пустой")
    if "Москва" not in prompt.user_prompt:
        raise AssertionError("Prompt не содержит данные запроса")


async def check_quota_service() -> None:
    tmp_dir = Path("logs")
    tmp_dir.mkdir(exist_ok=True)
    db_path = tmp_dir / "selftest-quota.db"
    if db_path.exists():
        db_path.unlink()
    db = Database(str(db_path))
    await db.init()
    qs = QuotaService(db, free_quota=2)
    await qs.ensure_user(42)
    before = await qs.get_free_left(42)
    if before != 2:
        raise AssertionError(f"Ожидалось 2 свободных запроса, получено {before}")
    consumed = await qs.consume_one(42)
    if not consumed:
        raise AssertionError("Не удалось списать квоту")
    after = await qs.get_free_left(42)
    if after != 1:
        raise AssertionError(f"Неверный остаток квоты: {after}")


async def main() -> None:
    results: list[TestResult] = []
    for name, func in [
        ("Router handlers", check_router_handlers),
        ("Callback coverage", check_callback_coverage),
        ("Prompt builder", check_prompt_builder),
    ]:
        try:
            func()
            results.append(TestResult(name, True))
        except Exception as exc:  # pragma: no cover - guard for selftest runner
            results.append(TestResult(name, False, str(exc)))

    try:
        await check_quota_service()
        results.append(TestResult("Quota service", True))
    except Exception as exc:  # pragma: no cover - guard
        results.append(TestResult("Quota service", False, str(exc)))

    for item in results:
        status = "OK" if item.success else "FAIL"
        message = f"[{status}] {item.name}"
        if item.details:
            message += f": {item.details}"
        print(message)

    if not all(r.success for r in results):
        raise SystemExit(1)

    print("ALL TESTS PASSED")


if __name__ == "__main__":
    asyncio.run(main())
