from __future__ import annotations

import asyncio
import json
import logging
import os
import platform
import subprocess
import sys
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest, TelegramUnauthorizedError

from app.config.runtime import runtime_config
from app.config.settings import settings
from app.core.logging import LOG_DIR, LOG_FILE
from app.services.ai_service import (
    AIServiceError,
    OpenAIService,
    StubAIService,
    resolve_ai_service,
)
from app.services.prompt_builder import HoroscopeRequest, build_horoscope_prompt
from app.tools.bot_runner import BotRunner
from app.tools.editor_store import EditorStore
from app.tools.env_manager import EnvManager
from app.tools.simulator import HoroscopeSimulator
from app.tools.ui_utils import (
    bind_clipboard_shortcuts,
    copy_text,
    open_path,
    paste_text,
    set_status,
)

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
        self.diagnostic_vars: dict[str, tk.StringVar] = {}
        self.status_var = tk.StringVar(value="Готово")
        self._ensure_env_file()
        self._build_ui()
        self._load_env_values()
        self._refresh_status_info()
        self.root.bind("<Control-s>", lambda _event: self._save_env())
        self.bot_runner.tail_logs(self._update_launch_logs)

    def _build_ui(self) -> None:
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True)

        notebook.add(self._tab_settings(notebook), text="Настройки")
        notebook.add(self._tab_diagnostics(notebook), text="Диагностика")
        notebook.add(self._tab_test_ai(notebook), text="Тест AI")
        notebook.add(self._tab_simulator(notebook), text="Симулятор")
        notebook.add(self._tab_launch(notebook), text="Запуск")
        notebook.add(self._tab_editor(notebook), text="Мини-редактор")

        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X)
        ttk.Label(status_frame, textvariable=self.status_var, anchor=tk.W).pack(
            fill=tk.X, padx=8, pady=4
        )

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
        secret_fields = {"BOT_TOKEN", "OPENAI_API_KEY"}

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
                entry = ttk.Entry(frame, width=50, show="*" if key in secret_fields else "")
                entry.grid(row=idx, column=1, sticky=tk.W, pady=2)
                bind_clipboard_shortcuts(entry)
                self.settings_entries[key] = entry
                btns = ttk.Frame(frame)
                btns.grid(row=idx, column=2, sticky=tk.W, pady=2)
                ttk.Button(btns, text="Копировать", command=lambda e=entry: self._copy_from_entry(e)).pack(side=tk.LEFT)
                ttk.Button(btns, text="Вставить", command=lambda e=entry: self._paste_to_entry(e)).pack(side=tk.LEFT, padx=2)
                ttk.Button(btns, text="Очистить", command=lambda e=entry: self._clear_entry(e)).pack(side=tk.LEFT, padx=2)
                if key in secret_fields:
                    ttk.Button(
                        btns,
                        text="Показать/Скрыть",
                        command=lambda e=entry: e.config(show="" if e.cget("show") else "*"),
                    ).pack(side=tk.LEFT, padx=2)

        btn_save = ttk.Button(frame, text="Сохранить .env", command=self._save_env)
        btn_save.grid(row=len(labels), column=0, pady=6, sticky=tk.W)
        btn_validate = ttk.Button(frame, text="Проверить .env", command=self._validate_env)
        btn_validate.grid(row=len(labels), column=1, pady=6, sticky=tk.W)
        ttk.Button(frame, text="Открыть .env", command=self._open_env_file).grid(
            row=len(labels), column=2, pady=6, sticky=tk.W
        )
        ttk.Button(frame, text="Проверить OpenAI", command=self._check_openai).grid(
            row=len(labels) + 1, column=0, pady=6, sticky=tk.W
        )
        self.openai_status = tk.StringVar()
        ttk.Label(frame, textvariable=self.openai_status, foreground="blue").grid(
            row=len(labels) + 1, column=1, sticky=tk.W
        )
        ttk.Button(frame, text="Открыть overrides", command=self._open_overrides).grid(
            row=len(labels) + 1, column=2, pady=6, sticky=tk.W
        )

        status_frame = ttk.LabelFrame(frame, text="Статус")
        status_frame.grid(row=len(labels) + 2, column=0, columnspan=3, sticky=tk.EW, pady=8)
        for idx, (label, value) in enumerate(self._diagnostic_info().items()):
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
        updates = self._diagnostic_info()
        for key, value in updates.items():
            if key in self.status_vars:
                self.status_vars[key].set(value)
            if key in self.diagnostic_vars:
                self.diagnostic_vars[key].set(value)

    def _set_status(self, text: str) -> None:
        set_status(self.status_var, text)
        self.root.update_idletasks()

    def _handle_error(self, title: str, exc: Exception) -> None:
        logger.exception("%s: %s", title, exc)
        try:
            messagebox.showerror(title, str(exc))
        except Exception:
            pass
        self._set_status(f"Ошибка: {title}")

    def _make_text_area(self, parent: tk.Misc, *, height: int = 6) -> tuple[ttk.Frame, tk.Text]:
        container = ttk.Frame(parent)
        text = tk.Text(container, height=height, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(container, command=text.yview)
        text.configure(yscrollcommand=scrollbar.set)
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        bind_clipboard_shortcuts(text)
        return container, text

    def _copy_from_text(self, widget: tk.Text) -> None:
        try:
            copy_text(self.root, widget.get("1.0", tk.END))
            self._set_status("Скопировано")
        except Exception as exc:  # pragma: no cover - runtime guard
            self._handle_error("Копирование", exc)

    def _copy_from_entry(self, widget: tk.Entry) -> None:
        try:
            copy_text(self.root, widget.get())
            self._set_status("Скопировано")
        except Exception as exc:  # pragma: no cover - runtime guard
            self._handle_error("Копирование", exc)

    def _paste_to_entry(self, widget: tk.Entry) -> None:
        try:
            widget.insert(tk.END, paste_text(self.root))
            self._set_status("Вставлено")
        except Exception as exc:  # pragma: no cover - runtime guard
            self._handle_error("Вставка", exc)

    def _paste_to_text(self, widget: tk.Text) -> None:
        try:
            widget.insert(tk.INSERT, paste_text(self.root))
            self._set_status("Вставлено")
        except Exception as exc:  # pragma: no cover - runtime guard
            self._handle_error("Вставка", exc)

    def _clear_text(self, widget: tk.Text) -> None:
        widget.delete("1.0", tk.END)
        self._set_status("Очищено")

    def _clear_entry(self, widget: tk.Entry) -> None:
        widget.delete(0, tk.END)
        self._set_status("Очищено")

    def _save_text_to_file(self, widget: tk.Text, title: str = "Сохранить в файл") -> None:
        try:
            content = widget.get("1.0", tk.END)
            path = filedialog.asksaveasfilename(
                defaultextension=".txt", filetypes=[("Text files", "*.txt"), ("All", "*.*")], title=title
            )
            if not path:
                return
            Path(path).write_text(content, encoding="utf-8")
            logger.info("Сохранён файл %s", path)
            self._set_status("Сохранено")
        except Exception as exc:  # pragma: no cover - runtime guard
            self._handle_error(title, exc)

    def _open_text_from_file(self, widget: tk.Text, title: str = "Открыть файл") -> None:
        try:
            path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt"), ("All", "*.*")], title=title)
            if not path:
                return
            content = Path(path).read_text(encoding="utf-8")
            widget.delete("1.0", tk.END)
            widget.insert(tk.END, content)
            logger.info("Загружен файл %s", path)
            self._set_status("Открыто")
        except Exception as exc:  # pragma: no cover - runtime guard
            self._handle_error(title, exc)

    def _diagnostic_info(self) -> dict[str, str]:
        venv_python = Path(".venv") / ("Scripts" if os.name == "nt" else "bin") / "python.exe"
        return {
            "Python": f"{platform.python_version()} ({sys.executable})",
            "Виртуальное окружение": f"{venv_python} ({'есть' if venv_python.exists() else 'нет'})",
            "Файл .env": f"{self.env_manager.path.resolve()} ({'есть' if self.env_manager.path.exists() else 'нет'})",
            "База данных": str(self._db_path().resolve()),
            "Каталог logs": str(LOG_DIR.resolve()),
        }

    def _tab_diagnostics(self, parent: ttk.Notebook) -> ttk.Frame:
        frame = ttk.Frame(parent, padding=10)

        env_frame = ttk.LabelFrame(frame, text="Среда")
        env_frame.pack(fill=tk.X, pady=4)
        for idx, (label, value) in enumerate(self._diagnostic_info().items()):
            ttk.Label(env_frame, text=label).grid(row=idx, column=0, sticky=tk.W, pady=2)
            var = tk.StringVar(value=value)
            self.diagnostic_vars[label] = var
            ttk.Label(env_frame, textvariable=var).grid(row=idx, column=1, sticky=tk.W, pady=2)

        btn_frame = ttk.LabelFrame(frame, text="Проверки")
        btn_frame.pack(fill=tk.X, pady=8)
        ttk.Button(btn_frame, text="Проверить зависимости", command=self._check_dependencies).grid(
            row=0, column=0, sticky=tk.W, pady=3
        )
        ttk.Button(btn_frame, text="Проверить токен Telegram", command=self._check_bot_token).grid(
            row=1, column=0, sticky=tk.W, pady=3
        )
        ttk.Button(btn_frame, text="Проверить OpenAI", command=self._check_openai_ping).grid(
            row=2, column=0, sticky=tk.W, pady=3
        )
        ttk.Button(btn_frame, text="Открыть логи", command=self._open_logs_folder).grid(
            row=3, column=0, sticky=tk.W, pady=3
        )

        self.diag_status = tk.StringVar(value="Готово")
        ttk.Label(frame, textvariable=self.diag_status, foreground="blue").pack(anchor=tk.W, pady=6)
        return frame

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
        self._set_status(".env сохранён")

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
            self._set_status("Проблемы в .env")
        else:
            logger.info(".env проверен, критичных проблем нет")
            messagebox.showinfo("OK", "Настройки выглядят корректно")
            self._set_status(".env проверен")

    def _set_diag_status(self, text: str, *, warn: bool = False) -> None:
        if hasattr(self, "diag_status"):
            self.diag_status.set(text)
        if warn:
            logger.warning(text)
        else:
            logger.info(text)

    def _check_dependencies(self) -> None:
        cmd = [
            sys.executable,
            "-c",
            "import aiogram, pydantic, pydantic_settings, aiosqlite; print('OK')",
        ]
        self._set_diag_status("Проверяю зависимости...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0 and "OK" in result.stdout:
            messagebox.showinfo("Зависимости", "aiogram/pydantic/aiosqlite доступны")
            logger.info("Проверка зависимостей: OK (%s)", result.stdout.strip())
            self._set_diag_status("Зависимости: OK")
        else:
            output = (result.stdout + result.stderr).strip()
            messagebox.showerror("Зависимости", f"Проблема: {output}")
            logger.error("Проблема с зависимостями: %s", output)
            self._set_diag_status("Зависимости: ошибка", warn=True)

    def _check_bot_token(self) -> None:
        env_settings = self.env_manager.load_settings()
        token = env_settings.bot_token
        if not token:
            message = "BOT_TOKEN пуст. Укажите токен в .env"
            logger.error(message)
            messagebox.showerror("Telegram", message)
            self._set_diag_status(message, warn=True)
            return

        async def _run() -> str:
            bot = Bot(token=token, parse_mode=ParseMode.HTML)
            me = await bot.get_me()
            await bot.session.close()
            return f"@{me.username}" if me.username else str(me.id)

        try:
            identifier = asyncio.run(_run())
            message = f"BOT_TOKEN OK: {identifier}"
            messagebox.showinfo("Telegram", message)
            logger.info(message)
            self._set_diag_status(message)
        except TelegramUnauthorizedError as exc:
            message = "BOT_TOKEN отклонен: проверьте значение"
            logger.error("%s (%s)", message, exc)
            messagebox.showerror("Telegram", message)
            self._set_diag_status(message, warn=True)
        except TelegramBadRequest as exc:
            message = f"Ошибка запроса к Telegram: {exc}"
            logger.error(message)
            messagebox.showerror("Telegram", message)
            self._set_diag_status(message, warn=True)
        except Exception as exc:  # pragma: no cover - runtime guard
            logger.exception("Не удалось проверить токен: %s", exc)
            messagebox.showerror("Telegram", f"Не удалось проверить токен: {exc}")
            self._set_diag_status("Проверка токена завершилась ошибкой", warn=True)

    def _check_openai_ping(self) -> None:
        self.openai_status.set("Выполняю запрос...")
        env = self.env_manager.load()
        use_openai = env.get("USE_OPENAI", "false").lower() == "true"
        api_key = env.get("OPENAI_API_KEY", "")
        req = HoroscopeRequest(
            mode="Технический пинг",
            birth_date="01.01.2000",
            birth_time=None,
            birth_place="Москва",
            gender="gender_o",
            focus="focus_general",
        )
        prompt = build_horoscope_prompt(req)

        if use_openai and not api_key:
            message = "USE_OPENAI=true, но OPENAI_API_KEY пуст — укажите ключ"
            logger.error(message)
            messagebox.showerror("OpenAI", message)
            self.openai_status.set(message)
            self._set_diag_status(message, warn=True)
            return

        if use_openai and api_key:
            try:
                service = OpenAIService(api_key)
                mode = "openai"
            except Exception as exc:  # pragma: no cover - runtime guard
                logger.exception("OpenAI SDK не инициализировался: %s", exc)
                messagebox.showerror("OpenAI", f"Не удалось инициализировать OpenAI: {exc}")
                self.openai_status.set(str(exc))
                self._set_diag_status("OpenAI не готов", warn=True)
                return
        else:
            service = StubAIService()
            mode = "stub"

        async def _run() -> str:
            return await service.generate(prompt)

        try:
            result = asyncio.run(_run())
            self.openai_status.set(result[:180] + ("..." if len(result) > 180 else ""))
            logger.info("OpenAI ping выполнен в режиме %s", mode)
            self._set_diag_status(f"OpenAI: {mode}")
        except AIServiceError as exc:
            self.openai_status.set(f"Ошибка: {exc}")
            logger.error("OpenAI ping error: %s", exc)
            messagebox.showerror("OpenAI", str(exc))
            self._set_diag_status("OpenAI ошибка", warn=True)
        except Exception as exc:  # pragma: no cover - runtime guard
            self.openai_status.set(f"Ошибка: {exc}")
            logger.exception("OpenAI ping error: %s", exc)
            messagebox.showerror("OpenAI", str(exc))
            self._set_diag_status("OpenAI ошибка", warn=True)

    def _check_openai(self) -> None:
        self._check_openai_ping()

    def _open_env_file(self) -> None:
        try:
            self.env_manager.path.touch(exist_ok=True)
            if open_path(self.env_manager.path.resolve()):
                self._set_status("Открыт .env")
            else:
                self._set_status("Ошибка открытия .env")
        except Exception as exc:  # pragma: no cover - runtime guard
            self._handle_error(".env", exc)

    def _open_file_path(self, path: Path) -> None:
        try:
            if open_path(Path(path).resolve()):
                self._set_status(f"Открыт файл {path}")
            else:
                self._set_status("Ошибка открытия файла")
        except Exception as exc:  # pragma: no cover - runtime guard
            self._handle_error("Файл", exc)

    def _open_logs_folder(self) -> None:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        path = LOG_DIR.resolve()
        try:
            if open_path(path):
                self._set_diag_status(f"Логи: {path}")
                self._set_status("Открыты логи")
            else:
                self._set_status("Ошибка открытия логов")
        except Exception as exc:  # pragma: no cover - runtime guard
            self._handle_error("Логи", exc)

    # --- Test AI tab
    def _tab_test_ai(self, parent: ttk.Notebook) -> ttk.Frame:
        frame = ttk.Frame(parent, padding=10)
        ttk.Label(frame, text="Пример входных данных (JSON)").pack(anchor=tk.W)
        ai_input_container, self.ai_input = self._make_text_area(frame, height=8)
        ai_input_container.pack(fill=tk.BOTH, expand=True)
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

        controls_input = ttk.Frame(frame)
        controls_input.pack(fill=tk.X, pady=3)
        ttk.Button(controls_input, text="Копировать", command=lambda: self._copy_from_text(self.ai_input)).pack(side=tk.LEFT)
        ttk.Button(controls_input, text="Вставить", command=lambda: self._paste_to_text(self.ai_input)).pack(side=tk.LEFT, padx=2)
        ttk.Button(controls_input, text="Очистить", command=lambda: self._clear_text(self.ai_input)).pack(side=tk.LEFT, padx=2)
        ttk.Button(controls_input, text="Сохранить в файл", command=lambda: self._save_text_to_file(self.ai_input, "Сохранить запрос")).pack(side=tk.LEFT, padx=2)
        ttk.Button(controls_input, text="Открыть файл", command=lambda: self._open_text_from_file(self.ai_input, "Открыть запрос")).pack(side=tk.LEFT, padx=2)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=4)
        ttk.Button(btn_frame, text="Сгенерировать prompt", command=self._build_prompt).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Вызвать AI", command=self._call_ai).pack(side=tk.LEFT, padx=5)

        prompt_container, self.prompt_box = self._make_text_area(frame, height=5)
        prompt_container.pack(fill=tk.BOTH, expand=True, pady=4)
        prompt_controls = ttk.Frame(frame)
        prompt_controls.pack(fill=tk.X)
        ttk.Button(prompt_controls, text="Копировать", command=lambda: self._copy_from_text(self.prompt_box)).pack(side=tk.LEFT)
        ttk.Button(prompt_controls, text="Вставить", command=lambda: self._paste_to_text(self.prompt_box)).pack(side=tk.LEFT, padx=2)
        ttk.Button(prompt_controls, text="Очистить", command=lambda: self._clear_text(self.prompt_box)).pack(side=tk.LEFT, padx=2)
        ttk.Button(prompt_controls, text="Сохранить в файл", command=lambda: self._save_text_to_file(self.prompt_box, "Сохранить prompt")).pack(side=tk.LEFT, padx=2)
        ttk.Button(prompt_controls, text="Открыть файл", command=lambda: self._open_text_from_file(self.prompt_box, "Открыть prompt")).pack(side=tk.LEFT, padx=2)

        output_container, self.ai_output = self._make_text_area(frame, height=5)
        output_container.pack(fill=tk.BOTH, expand=True, pady=4)
        output_controls = ttk.Frame(frame)
        output_controls.pack(fill=tk.X)
        ttk.Button(output_controls, text="Копировать", command=lambda: self._copy_from_text(self.ai_output)).pack(side=tk.LEFT)
        ttk.Button(output_controls, text="Вставить", command=lambda: self._paste_to_text(self.ai_output)).pack(side=tk.LEFT, padx=2)
        ttk.Button(output_controls, text="Очистить", command=lambda: self._clear_text(self.ai_output)).pack(side=tk.LEFT, padx=2)
        ttk.Button(output_controls, text="Сохранить в файл", command=lambda: self._save_text_to_file(self.ai_output, "Сохранить ответ")).pack(side=tk.LEFT, padx=2)
        ttk.Button(output_controls, text="Открыть файл", command=lambda: self._open_text_from_file(self.ai_output, "Открыть ответ")).pack(side=tk.LEFT, padx=2)

        self.ai_error = tk.StringVar()
        ttk.Label(frame, textvariable=self.ai_error, foreground="red").pack(anchor=tk.W)
        return frame

    def _parse_ai_input(self) -> HoroscopeRequest | None:
        try:
            data = json.loads(self.ai_input.get("1.0", tk.END))
            return HoroscopeRequest(**data)
        except Exception as exc:
            self.ai_error.set(f"Ошибка ввода: {exc}")
            logger.exception("Ошибка парсинга ввода AI: %s", exc)
            self._set_status("Ошибка ввода AI")
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
        self._set_status("Prompt сгенерирован")

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
                self._set_status("Ответ AI получен")
            except Exception as exc:  # pragma: no cover - runtime guard
                self.ai_error.set(str(exc))
                self._handle_error("AI тест", exc)

        asyncio.run(_run())

    def _copy_ai_result(self) -> None:
        self._copy_from_text(self.ai_output)

    # --- Simulator tab
    def _tab_simulator(self, parent: ttk.Notebook) -> ttk.Frame:
        frame = ttk.Frame(parent, padding=10)
        left = ttk.Frame(frame)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        right = ttk.Frame(frame)
        right.pack(side=tk.RIGHT, fill=tk.Y, padx=6)

        history_container, self.sim_history = self._make_text_area(left, height=20)
        history_container.pack(fill=tk.BOTH, expand=True)
        history_controls = ttk.Frame(left)
        history_controls.pack(fill=tk.X, pady=4)
        ttk.Button(history_controls, text="Копировать весь лог симуляции", command=lambda: self._copy_from_text(self.sim_history)).pack(side=tk.LEFT)
        ttk.Button(history_controls, text="Вставить", command=lambda: self._paste_to_text(self.sim_history)).pack(side=tk.LEFT, padx=2)
        ttk.Button(history_controls, text="Очистить", command=lambda: self._clear_text(self.sim_history)).pack(side=tk.LEFT, padx=2)
        ttk.Button(history_controls, text="Сохранить", command=lambda: self._save_text_to_file(self.sim_history, "Сохранить симуляцию")).pack(side=tk.LEFT, padx=2)
        ttk.Button(history_controls, text="Открыть", command=lambda: self._open_text_from_file(self.sim_history, "Открыть симуляцию")).pack(side=tk.LEFT, padx=2)

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
            bind_clipboard_shortcuts(entry)
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
        self._set_status("Демо-данные подставлены")

    def _simulate_request(self) -> None:
        values = {key: entry.get() or None for key, entry in self.sim_entries.items()}
        self.simulator.set_values(values)

        async def _run() -> str:
            return await self.simulator.simulate()

        result = asyncio.run(_run())
        self.sim_history.insert(tk.END, f"USER: {values}\nBOT: {result}\n---\n")
        self._set_status("Симуляция выполнена")

    def _reset_simulation(self) -> None:
        self.simulator.reset()
        self.sim_history.delete("1.0", tk.END)
        self._set_status("Симуляция сброшена")

    # --- Launch tab
    def _tab_launch(self, parent: ttk.Notebook) -> ttk.Frame:
        frame = ttk.Frame(parent, padding=10)
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="Запустить бота", command=self._start_bot).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Остановить бота", command=self._stop_bot).pack(side=tk.LEFT, padx=5)
        ttk.Label(frame, text=f"Лог: {LOG_FILE}").pack(anchor=tk.W, pady=2)
        launch_container, self.launch_logs = self._make_text_area(frame, height=20)
        launch_container.pack(fill=tk.BOTH, expand=True, pady=6)
        controls = ttk.Frame(frame)
        controls.pack(fill=tk.X)
        ttk.Button(controls, text="Копировать", command=lambda: self._copy_from_text(self.launch_logs)).pack(side=tk.LEFT)
        ttk.Button(controls, text="Вставить", command=lambda: self._paste_to_text(self.launch_logs)).pack(side=tk.LEFT, padx=2)
        ttk.Button(controls, text="Очистить", command=lambda: self._clear_text(self.launch_logs)).pack(side=tk.LEFT, padx=2)
        ttk.Button(controls, text="Сохранить", command=lambda: self._save_text_to_file(self.launch_logs, "Сохранить лог")).pack(side=tk.LEFT, padx=2)
        ttk.Button(controls, text="Открыть файл лога", command=lambda: self._open_file_path(LOG_FILE)).pack(side=tk.LEFT, padx=2)
        return frame

    def _start_bot(self) -> None:
        try:
            self.bot_runner.start()
            messagebox.showinfo("Бот", "Бот запущен")
            logger.info("Бот запущен из GUI")
            self._set_status("Бот запущен")
        except Exception as exc:  # pragma: no cover - runtime guard
            logger.exception("Не удалось запустить бота: %s", exc)
            messagebox.showerror("Ошибка", f"Не удалось запустить бота: {exc}")

    def _stop_bot(self) -> None:
        self.bot_runner.stop()
        logger.info("Бот остановлен")
        messagebox.showinfo("Бот", "Бот остановлен")
        self._set_status("Бот остановлен")

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
            bind_clipboard_shortcuts(entry)
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
        self._set_status("Overrides сохранены")

    def _apply_overrides(self) -> None:
        runtime_config.reload()
        messagebox.showinfo("Overrides", "Перезагружено. Применится при перезапуске бота")
        self._set_status("Overrides обновлены")

    def _open_overrides(self) -> None:
        try:
            if open_path(self.editor_store.path.resolve()):
                self._set_status("Открыт overrides")
            else:
                self._set_status("Ошибка открытия overrides")
        except Exception as exc:  # pragma: no cover - runtime guard
            self._handle_error("Overrides", exc)


def start_gui() -> None:
    setup_launcher_logging()
    try:
        LauncherGUI().run()
    except Exception as exc:  # pragma: no cover - runtime guard
        logger.exception("Launcher crashed: %s", exc)
        try:
            messagebox.showerror("Launcher error", f"{exc}\nОткройте {LAUNCHER_LOG} для деталей")
        except Exception:
            print(f"Launcher error: {exc}")

