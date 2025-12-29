from __future__ import annotations

import argparse
import asyncio
import json
import sys

from app.config.runtime import runtime_config
from app.services.ai_service import resolve_ai_service
from app.services.prompt_builder import HoroscopeRequest, build_horoscope_prompt
from app.tools.env_manager import EnvManager
from app.tools.launcher_gui import start_gui


def run_bot_cli() -> None:
    from bot import main
    from app.services.health import perform_startup_checks

    perform_startup_checks()
    asyncio.run(main())


def run_test_ai() -> None:
    req = HoroscopeRequest(
        mode="Прогноз на сегодня",
        birth_date="01.01.1990",
        birth_time="08:00",
        birth_place="Москва",
        gender="gender_f",
        focus="focus_general",
    )
    prompt = build_horoscope_prompt(req)
    print("Prompt (system):\n", prompt.system_prompt)
    print("Prompt (user):\n", prompt.user_prompt)

    async def _call() -> None:
        ai_resolution = resolve_ai_service()
        print(f"AI mode: {ai_resolution.mode}")
        try:
            result = await ai_resolution.service.generate(prompt)
            print("\nОтвет AI:\n", result)
        except Exception as exc:  # pragma: no cover - runtime guard
            print("Ошибка AI:", exc)

    asyncio.run(_call())


def print_env() -> None:
    env = EnvManager().load()
    masked = EnvManager().masked_env(env)
    print(json.dumps(masked, ensure_ascii=False, indent=2))
    print("Overrides:", runtime_config.overrides_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="GOROSKOPE launcher")
    parser.add_argument("--run-bot", action="store_true", help="Запустить бота без GUI")
    parser.add_argument("--test-ai", action="store_true", help="Проверить AI и промпт")
    parser.add_argument("--print-env", action="store_true", help="Показать настройки")
    args = parser.parse_args()

    if args.run_bot:
        run_bot_cli()
        return
    if args.test_ai:
        run_test_ai()
        return
    if args.print_env:
        print_env()
        return

    start_gui()


if __name__ == "__main__":
    main()

