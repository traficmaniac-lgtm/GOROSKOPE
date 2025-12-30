from __future__ import annotations

import argparse
import asyncio
import json
import logging
import subprocess
import sys

from app.config.runtime import runtime_config
from app.services.ai_service import resolve_ai_service
from app.services.prompt_builder import HoroscopeRequest, build_horoscope_prompt
from app.tools.env_manager import EnvManager
from app.tools.launcher_gui import LAUNCHER_LOG, setup_launcher_logging, start_gui


def run_bot_cli() -> None:
    from bot import main
    from app.services.health import StartupError, perform_startup_checks

    try:
        perform_startup_checks()
    except StartupError as exc:
        print(f"Ошибка запуска бота: {exc}")
        return
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


def run_selftest() -> None:
    """Запуск встроенного набора проверок без GUI."""

    command = [sys.executable, "tools/selftest.py"]
    print("Запускаю selftest:", " ".join(command))
    try:
        result = subprocess.run(command, check=False, capture_output=True, text=True)
    except FileNotFoundError:
        print("tools/selftest.py не найден. Убедитесь, что файл на месте.")
        return

    if result.stdout:
        print(result.stdout.strip())
    if result.stderr:
        print(result.stderr.strip())

    if result.returncode == 0:
        print("SELFTEST: OK")
    else:
        print(f"SELFTEST завершился с кодом {result.returncode}")


def main() -> None:
    parser = argparse.ArgumentParser(description="GOROSKOPE launcher")
    parser.add_argument("--run-bot", action="store_true", help="Запустить бота без GUI")
    parser.add_argument("--test-ai", action="store_true", help="Проверить AI и промпт")
    parser.add_argument("--print-env", action="store_true", help="Показать настройки")
    parser.add_argument("--selftest", action="store_true", help="Запустить самопроверку")
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
    if args.selftest:
        run_selftest()
        return

    setup_launcher_logging()
    try:
        start_gui()
    except Exception as exc:  # pragma: no cover - runtime guard
        logging.getLogger("launcher").exception("GUI failed: %s", exc)
        try:
            from tkinter import messagebox

            messagebox.showerror(
                "Launcher error", f"{exc}\nОткройте {LAUNCHER_LOG} для деталей"
            )
        except Exception:
            print(f"Launcher error: {exc}. Подробности: {LAUNCHER_LOG}")


if __name__ == "__main__":
    main()

