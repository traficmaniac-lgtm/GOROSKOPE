from __future__ import annotations

import asyncio
import json
import logging
import platform
import sys
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

from app.config.runtime import runtime_config
from app.config.settings import settings
from app.core.logging import LOG_DIR, LOG_FILE
from app.services.ai_service import resolve_ai_service
from app.services.prompt_builder import HoroscopeRequest, build_horoscope_prompt
from app.tools.bot_runner import BotRunner
from app.tools.editor_store import EditorStore
from app.tools.env_manager import EnvManager
from app.tools.simulator import HoroscopeSimulator

LAUNCHER_LOG = LOG_DIR / "launcher.log"


def setup_launcher_logging() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger.setLevel(logging.INFO)
    if logger.handlers:
        return
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    file_handler = logging.FileHandler(LAUNCHER_LOG, encoding="utf-8")
    file_handler.setFormatter(formatter)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


logger = logging.getLogger("launcher")


class LauncherGUI:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("GOROSKOPE Launcher")
        self.env_manager = EnvManager()
        self.editor_store = EditorStore()
        self.bot_runner = BotRunner()
        self.simulator = HoroscopeSimulator()
        self.status_vars: dict[str, tk.StringVar] = {}
        self._ensure_env_file()
        self._build_ui()
        self._load_env_values()
        self._refresh_status_info()
        self.bot_runner.tail_logs(self._update_launch_logs)

    def _build_ui(self) -> None:
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True)

        notebook.add(self._tab_settings(notebook), text="Настройки")
        notebook.add(self._tab_test_ai(notebook), text="Тест AI")
        notebook.add(self._tab_simulator(notebook), text="Симулятор")
        notebook.add(self._tab_launch(notebook), text="Запуск")
        notebook.add(self._tab_editor(notebook), text="Мини-редактор")

    def run(self) -> None:
        self.root.mainloop()

    def _ensure_env_file(self) -> None:
        if self.env_manager.path.exists():
            return
        created = False
        example_path = Path(".env.example")
        if example_path.exists():
            if messagebox.askyesno(".env", "Файл .env не найден. Создать копию .env.example?"):
                created = self.env_manager.create_from_example(example_path)
                if created:
                    logger.info("Создан .env из .env.example")
        if not created:
            self.env_manager.ensure_exists()
            logger.info("Создан пустой .env")

    # --- Settings tab
    def _tab_settings(self, parent: ttk.Notebook) -> ttk.Frame:
        frame = ttk.Frame(parent, padding=10)
        labels = ["BOT_TOKEN", "USE_OPENAI", "OPENAI_API_KEY", "LOG_LEVEL", "DB_PATH"]
        self.settings_entries: dict[str, tk.Widget] = {}

        for idx, key in enumerate(labels):
            ttk.Label(frame, text=key).grid(row=idx, column=0, sticky=tk.W, pady=2)
            if key == "USE_OPENAI":
                var = tk.BooleanVar()
                chk = ttk.Checkbutton(frame, variable=var)
                chk.grid(row=idx, column=1, sticky=tk.W, pady=2)
                self.settings_entries[key] = chk
                self.use_openai_var = var
            elif key == "LOG_LEVEL":
                combo = ttk.Combobox(frame, values=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], width=47)
                combo.grid(row=idx, column=1, sticky=tk.W, pady=2)
                combo.set("INFO")
                self.settings_entries[key] = combo
            else:
                entry = ttk.Entry(frame, width=50)
                entry.grid(row=idx, column=1, sticky=tk.W, pady=2)
                self.settings_entries[key] = entry

        btn_save = ttk.Button(frame, text="Сохранить .env", command=self._save_env)
        btn_save.grid(row=len(labels), column=0, pady=6, sticky=tk.W)
        btn_validate = ttk.Button(frame, text="Проверить .env", command=self._validate_env)
        btn_validate.grid(row=len(labels), column=1, pady=6, sticky=tk.W)
        ttk.Button(frame, text="Проверить OpenAI", command=self._check_openai).grid(
            row=len(labels) + 1, column=0, pady=6, sticky=tk.W
        )
        self.openai_status = tk.StringVar()
        ttk.Label(frame, textvariable=self.openai_status, foreground="blue").grid(
            row=len(labels) + 1, column=1, sticky=tk.W
        )

        status_frame = ttk.LabelFrame(frame, text="Статус")
        status_frame.grid(row=len(labels) + 2, column=0, columnspan=2, sticky=tk.EW, pady=8)
        status_items = {
            "Python": f"{platform.python_version()} ({sys.executable})",
            "Виртуальное окружение": str(Path(".venv").resolve()),
            "Файл .env": str(self.env_manager.path.resolve()),
            "База данных": str(self._db_path().resolve()),
            "Логи": str(LOG_FILE.resolve()),
        }
        for idx, (label, value) in enumerate(status_items.items()):
            ttk.Label(status_frame, text=label).grid(row=idx, column=0, sticky=tk.W, pady=2)
            var = tk.StringVar(value=value)
            self.status_vars[label] = var
            ttk.Label(status_frame, textvariable=var).grid(row=idx, column=1, sticky=tk.W, pady=2)
        return frame

    def _load_env_values(self) -> None:
        env = self.env_manager.load()
        for key, widget in self.settings_entries.items():
            value = env.get(key, "")
            if isinstance(widget, ttk.Combobox):
                widget.set(value or "INFO")
            elif isinstance(widget, ttk.Checkbutton):
                self.use_openai_var.set(value.lower() == "true")
            elif isinstance(widget, tk.Entry):
                widget.delete(0, tk.END)
                widget.insert(0, value)

    def _db_path(self) -> Path:
        env = self.env_manager.load()
        return Path(env.get("DB_PATH") or settings.db_path)

    def _refresh_status_info(self) -> None:
        updates = {
            "Python": f"{platform.python_version()} ({sys.executable})",
            "Виртуальное окружение": str(Path(".venv").resolve()),
            "Файл .env": str(self.env_manager.path.resolve()),
            "База данных": str(self._db_path().resolve()),
            "Логи": str(LOG_FILE.resolve()),
        }
        for key, value in updates.items():
            if key in self.status_vars:
                self.status_vars[key].set(value)

    def _save_env(self) -> None:
        values: dict[str, str] = {}
        for key, widget in self.settings_entries.items():
            if isinstance(widget, ttk.Combobox):
                values[key] = widget.get()
            elif isinstance(widget, ttk.Checkbutton):
                values[key] = "true" if self.use_openai_var.get() else "false"
            elif isinstance(widget, tk.Entry):
                values[key] = widget.get()
        self.env_manager.save(values)
        logger.info(".env сохранён: %s", values.keys())
        self._refresh_status_info()
        messagebox.showinfo("Готово", ".env сохранён")

    def _validate_env(self) -> None:
        env: dict[str, str] = {}
        for key, widget in self.settings_entries.items():
            if isinstance(widget, ttk.Combobox):
                env[key] = widget.get()
            elif isinstance(widget, ttk.Checkbutton):
                env[key] = "true" if self.use_openai_var.get() else "false"
            elif isinstance(widget, tk.Entry):
                env[key] = widget.get()
        errors = self.env_manager.validate(env)
        if errors:
            logger.warning("Проблемы в .env: %s", errors)
            messagebox.showwarning("Проблемы", "\n".join(errors))
        else:
            logger.info(".env проверен, критичных проблем нет")
            messagebox.showinfo("OK", "Настройки выглядят корректно")

    def _check_openai(self) -> None:
        self.openai_status.set("Выполняю запрос...")
        req = HoroscopeRequest(
            mode="Технический пинг",
            birth_date="01.01.2000",
            birth_time=None,
            birth_place="Москва",
            gender="gender_o",
            focus="focus_general",
        )
        prompt = build_horoscope_prompt(req)

        async def _run() -> tuple[str, str]:
            resolution = resolve_ai_service()
            return await resolution.service.generate(prompt), resolution.mode

        try:
            result, mode = asyncio.run(_run())
            self.openai_status.set(result[:180] + ("..." if len(result) > 180 else ""))
            logger.info("OpenAI ping выполнен в режиме %s", mode)
        except Exception as exc:  # pragma: no cover - runtime guard
            self.openai_status.set(f"Ошибка: {exc}")
            logger.exception("OpenAI ping error: %s", exc)

    # --- Test AI tab
    def _tab_test_ai(self, parent: ttk.Notebook) -> ttk.Frame:
        frame = ttk.Frame(parent, padding=10)
        ttk.Label(frame, text="Пример входных данных (JSON)").pack(anchor=tk.W)
        self.ai_input = tk.Text(frame, height=6)
        self.ai_input.pack(fill=tk.X)
        self.ai_input.insert(
            tk.END,
            json.dumps(
                {
                    "mode": "Прогноз на сегодня",
                    "birth_date": "01.01.1990",
                    "birth_time": "08:00",
                    "birth_place": "Москва",
                    "gender": "gender_f",
                    "focus": "focus_general",
                },
                ensure_ascii=False,
                indent=2,
            ),
        )

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=4)
        ttk.Button(btn_frame, text="Сгенерировать prompt", command=self._build_prompt).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Вызвать AI", command=self._call_ai).pack(side=tk.LEFT, padx=5)

        self.prompt_box = tk.Text(frame, height=5)
        self.prompt_box.pack(fill=tk.BOTH, expand=True, pady=4)
        self.ai_output = tk.Text(frame, height=5)
        self.ai_output.pack(fill=tk.BOTH, expand=True, pady=4)
        ttk.Button(frame, text="Копировать результат", command=self._copy_ai_result).pack(anchor=tk.E)
        self.ai_error = tk.StringVar()
        ttk.Label(frame, textvariable=self.ai_error, foreground="red").pack(anchor=tk.W)
        return frame

    def _parse_ai_input(self) -> HoroscopeRequest | None:
        try:
            data = json.loads(self.ai_input.get("1.0", tk.END))
            return HoroscopeRequest(**data)
        except Exception as exc:
            self.ai_error.set(f"Ошибка ввода: {exc}")
            return None

    def _build_prompt(self) -> None:
        self.ai_error.set("")
        req = self._parse_ai_input()
        if not req:
            return
        prompt = build_horoscope_prompt(req)
        self.prompt_box.delete("1.0", tk.END)
        self.prompt_box.insert(
            tk.END, f"SYSTEM:\n{prompt.system_prompt}\n\nUSER:\n{prompt.user_prompt}"
        )

    def _call_ai(self) -> None:
        self.ai_error.set("")
        req = self._parse_ai_input()
        if not req:
            return
        prompt = build_horoscope_prompt(req)

        async def _run() -> None:
            try:
                ai_resolution = resolve_ai_service()
                result = await ai_resolution.service.generate(prompt)
                self.ai_output.delete("1.0", tk.END)
                self.ai_output.insert(tk.END, f"[{ai_resolution.mode}]\n{result}")
                logger.info("AI тест выполнен в режиме %s", ai_resolution.mode)
            except Exception as exc:  # pragma: no cover - runtime guard
                self.ai_error.set(str(exc))
                logger.exception("AI тест завершился ошибкой: %s", exc)

        asyncio.run(_run())

    def _copy_ai_result(self) -> None:
        text = self.ai_output.get("1.0", tk.END)
        self.root.clipboard_clear()
        self.root.clipboard_append(text)

    # --- Simulator tab
    def _tab_simulator(self, parent: ttk.Notebook) -> ttk.Frame:
        frame = ttk.Frame(parent, padding=10)
        left = ttk.Frame(frame)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        right = ttk.Frame(frame)
        right.pack(side=tk.RIGHT, fill=tk.Y, padx=6)

        self.sim_history = tk.Text(left, height=20)
        self.sim_history.pack(fill=tk.BOTH, expand=True)

        fields = [
            ("mode", "Прогноз на сегодня"),
            ("birth_date", "01.01.1990"),
            ("birth_time", "08:00"),
            ("birth_place", "Москва"),
            ("gender", "gender_f"),
            ("focus", "focus_general"),
            ("action", "hs_today"),
        ]
        self.sim_entries: dict[str, tk.Entry] = {}
        for idx, (key, default) in enumerate(fields):
            ttk.Label(right, text=key).grid(row=idx, column=0, sticky=tk.W, pady=2)
            entry = ttk.Entry(right)
            entry.insert(0, default)
            entry.grid(row=idx, column=1, pady=2)
            self.sim_entries[key] = entry

        ttk.Button(right, text="Пройти сценарий автоматически", command=self._fill_sim_demo).grid(
            row=len(fields), column=0, columnspan=2, pady=4, sticky=tk.EW
        )
        ttk.Button(right, text="Симулировать запрос", command=self._simulate_request).grid(
            row=len(fields) + 1, column=0, columnspan=2, pady=4, sticky=tk.EW
        )
        ttk.Button(right, text="Сбросить симуляцию", command=self._reset_simulation).grid(
            row=len(fields) + 2, column=0, columnspan=2, pady=4, sticky=tk.EW
        )
        return frame

    def _fill_sim_demo(self) -> None:
        for key, entry in self.sim_entries.items():
            entry.delete(0, tk.END)
        demo = {
            "mode": "Прогноз на неделю",
            "birth_date": "12.12.1995",
            "birth_time": "07:30",
            "birth_place": "Санкт-Петербург",
            "gender": "gender_m",
            "focus": "focus_career",
            "action": "hs_week",
        }
        for key, value in demo.items():
            self.sim_entries[key].insert(0, value)

    def _simulate_request(self) -> None:
        values = {key: entry.get() or None for key, entry in self.sim_entries.items()}
        self.simulator.set_values(values)

        async def _run() -> str:
            return await self.simulator.simulate()

        result = asyncio.run(_run())
        self.sim_history.insert(tk.END, f"USER: {values}\nBOT: {result}\n---\n")

    def _reset_simulation(self) -> None:
        self.simulator.reset()
        self.sim_history.delete("1.0", tk.END)

    # --- Launch tab
    def _tab_launch(self, parent: ttk.Notebook) -> ttk.Frame:
        frame = ttk.Frame(parent, padding=10)
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="Запустить бота", command=self._start_bot).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Остановить бота", command=self._stop_bot).pack(side=tk.LEFT, padx=5)
        ttk.Label(frame, text=f"Лог: {LOG_FILE}").pack(anchor=tk.W, pady=2)
        self.launch_logs = tk.Text(frame, height=20)
        self.launch_logs.pack(fill=tk.BOTH, expand=True, pady=6)
        return frame

    def _start_bot(self) -> None:
        try:
            self.bot_runner.start()
            messagebox.showinfo("Бот", "Бот запущен")
            logger.info("Бот запущен из GUI")
        except Exception as exc:  # pragma: no cover - runtime guard
            logger.exception("Не удалось запустить бота: %s", exc)
            messagebox.showerror("Ошибка", f"Не удалось запустить бота: {exc}")

    def _stop_bot(self) -> None:
        self.bot_runner.stop()
        logger.info("Бот остановлен")
        messagebox.showinfo("Бот", "Бот остановлен")

    def _update_launch_logs(self, text: str) -> None:
        tail = "\n".join(text.splitlines()[-200:])
        self.launch_logs.delete("1.0", tk.END)
        self.launch_logs.insert(tk.END, tail)

    # --- Editor tab
    def _tab_editor(self, parent: ttk.Notebook) -> ttk.Frame:
        frame = ttk.Frame(parent, padding=10)
        fields = [
            ("FREE_QUOTA", runtime_config.free_quota),
            ("REQUEST_PRICE_STARS", settings.request_price_stars),
            ("ABOUT", ""),
            ("LIMIT_EXHAUSTED", ""),
            ("MAIN_MENU_TITLE", ""),
            ("PROMPT_TONE", runtime_config.prompt_style.get("tone", "")),
            ("PROMPT_BULLETS", runtime_config.prompt_style.get("bullets_count") or ""),
        ]
        self.editor_entries: dict[str, tk.Entry] = {}
        for idx, (label, default) in enumerate(fields):
            ttk.Label(frame, text=label).grid(row=idx, column=0, sticky=tk.W, pady=2)
            entry = ttk.Entry(frame, width=50)
            entry.insert(0, str(default))
            entry.grid(row=idx, column=1, pady=2)
            self.editor_entries[label] = entry

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=len(fields), column=0, columnspan=2, pady=6)
        ttk.Button(btn_frame, text="Сохранить overrides", command=self._save_overrides).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Применить overrides", command=self._apply_overrides).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Открыть файл overrides", command=self._open_overrides).pack(side=tk.LEFT)
        return frame

    def _save_overrides(self) -> None:
        data = self.editor_store.load()
        data["FREE_QUOTA"] = int(self.editor_entries["FREE_QUOTA"].get() or 0)
        data["REQUEST_PRICE_STARS"] = int(self.editor_entries["REQUEST_PRICE_STARS"].get() or 0)
        data.setdefault("TEXTS", {})
        for key in ["ABOUT", "LIMIT_EXHAUSTED", "MAIN_MENU_TITLE"]:
            value = self.editor_entries[key].get()
            if value:
                data["TEXTS"][key] = value
        data["HOROSCOPE_PROMPT_STYLE"] = {
            "tone": self.editor_entries["PROMPT_TONE"].get() or None,
            "bullets": int(self.editor_entries["PROMPT_BULLETS"].get() or 0) or None,
        }
        self.editor_store.save(data)
        messagebox.showinfo("Overrides", "Сохранено в bot_overrides.json")

    def _apply_overrides(self) -> None:
        runtime_config.reload()
        messagebox.showinfo("Overrides", "Перезагружено. Применится при перезапуске бота")

    def _open_overrides(self) -> None:
        path = self.editor_store.path
        messagebox.showinfo("Overrides", f"Файл: {path.resolve()}")


def start_gui() -> None:
    setup_launcher_logging()
    try:
        LauncherGUI().run()
    except Exception as exc:  # pragma: no cover - runtime guard
        logger.exception("Launcher crashed: %s", exc)
        try:
            messagebox.showerror("Launcher error", str(exc))
        except Exception:
            print(f"Launcher error: {exc}")

