"""Tkinter control panel for managing the bot."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from tkinter import BOTH, END, LEFT, RIGHT, Button, Entry, Frame, Label, Scrollbar, Text, Tk, messagebox

from app import config
from app.bot import SETTINGS_DEFAULTS, load_settings

LOG_FILE = config.LOG_DIR / "bot.log"
PYTHON_PATH = Path(".venv") / "Scripts" / "python.exe"


class ControlPanel:
    def __init__(self, root: Tk) -> None:
        self.root = root
        self.root.title("GOROSKOPE Control Panel")
        self.bot_process: subprocess.Popen | None = None
        config.ensure_directories()

        self.env_values = self._read_env()
        self.settings = load_settings()

        self._build_form()
        self._build_logs()
        self._refresh_logs()

    def _build_form(self) -> None:
        form = Frame(self.root)
        form.pack(fill=BOTH, padx=10, pady=10)

        self.token_entry = self._add_field(form, "TELEGRAM_BOT_TOKEN", self.env_values.get("TELEGRAM_BOT_TOKEN", ""))
        self.openai_entry = self._add_field(form, "OPENAI_API_KEY", self.env_values.get("OPENAI_API_KEY", ""))
        self.model_entry = self._add_field(form, "OPENAI_MODEL", self.env_values.get("OPENAI_MODEL", config.DEFAULT_MODEL))
        self.admin_entry = self._add_field(form, "ADMIN_TELEGRAM_ID", self.env_values.get("ADMIN_TELEGRAM_ID", ""))

        Label(form, text="Welcome message (/start)").pack(anchor="w", pady=(10, 0))
        self.welcome_text = Text(form, height=3, width=70)
        self.welcome_text.pack(fill=BOTH)
        self.welcome_text.insert("1.0", self.settings.get("welcome_message", SETTINGS_DEFAULTS["welcome_message"]))

        Label(form, text="System prompt").pack(anchor="w", pady=(10, 0))
        self.system_text = Text(form, height=5, width=70)
        self.system_text.pack(fill=BOTH)
        self.system_text.insert("1.0", self.settings.get("system_prompt", SETTINGS_DEFAULTS["system_prompt"]))

        buttons = Frame(form)
        buttons.pack(fill=BOTH, pady=10)
        Button(buttons, text="Save settings", command=self.save_settings).pack(side=LEFT, padx=5)
        Button(buttons, text="Start bot", command=self.start_bot).pack(side=LEFT, padx=5)
        Button(buttons, text="Stop bot", command=self.stop_bot).pack(side=LEFT, padx=5)
        Button(buttons, text="Open logs folder", command=self.open_logs).pack(side=LEFT, padx=5)

    def _build_logs(self) -> None:
        frame = Frame(self.root)
        frame.pack(fill=BOTH, expand=True, padx=10, pady=(0, 10))
        Label(frame, text="Logs").pack(anchor="w")
        self.log_text = Text(frame, height=12)
        self.log_text.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar = Scrollbar(frame)
        scrollbar.pack(side=RIGHT, fill='y')
        self.log_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.log_text.yview)

    def _add_field(self, parent: Frame, label: str, value: str) -> Entry:
        row = Frame(parent)
        row.pack(fill=BOTH, pady=2)
        Label(row, text=label, width=20, anchor="w").pack(side=LEFT)
        entry = Entry(row, width=50)
        entry.pack(side=LEFT, fill=BOTH, expand=True)
        entry.insert(0, value)
        return entry

    def _read_env(self) -> dict:
        config.load_env()
        result = {}
        if config.ENV_FILE.exists():
            with config.ENV_FILE.open("r", encoding="utf-8") as f:
                for line in f:
                    if "=" in line:
                        k, v = line.strip().split("=", 1)
                        result[k] = v
        return result

    def save_settings(self) -> None:
        token = self.token_entry.get().strip()
        openai_key = self.openai_entry.get().strip()
        model = self.model_entry.get().strip() or config.DEFAULT_MODEL
        admin = self.admin_entry.get().strip()

        if not token or not openai_key:
            messagebox.showwarning("Внимание", "Токен бота и ключ OpenAI могут быть пустыми, но бот не запустится.")

        config.update_env_file(
            TELEGRAM_BOT_TOKEN=token,
            OPENAI_API_KEY=openai_key,
            OPENAI_MODEL=model,
            ADMIN_TELEGRAM_ID=admin,
        )

        self.settings = {
            "welcome_message": self.welcome_text.get("1.0", END).strip() or SETTINGS_DEFAULTS["welcome_message"],
            "system_prompt": self.system_text.get("1.0", END).strip() or SETTINGS_DEFAULTS["system_prompt"],
        }
        SETTINGS_FILE = config.SETTINGS_FILE
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        SETTINGS_FILE.write_text(
            json.dumps(self.settings, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        messagebox.showinfo("Сохранено", "Настройки обновлены.")

    def start_bot(self) -> None:
        if self.bot_process and self.bot_process.poll() is None:
            messagebox.showinfo("Бот", "Бот уже запущен.")
            return
        python_path = PYTHON_PATH if PYTHON_PATH.exists() else sys.executable
        cmd = [str(python_path), "-m", "app.bot"]
        try:
            self.bot_process = subprocess.Popen(cmd, cwd=Path(__file__).resolve().parent.parent)
            messagebox.showinfo("Бот", "Бот запущен.")
        except FileNotFoundError:
            messagebox.showerror("Ошибка", "Не найден .venv. Запустите 00_setup_repo.ps1")
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Ошибка", f"Не удалось запустить бота: {exc}")

    def stop_bot(self) -> None:
        if self.bot_process and self.bot_process.poll() is None:
            self.bot_process.terminate()
            self.bot_process.wait(timeout=5)
            messagebox.showinfo("Бот", "Бот остановлен.")
        else:
            messagebox.showinfo("Бот", "Бот не запущен.")

    def open_logs(self) -> None:
        LOG_DIR = config.LOG_DIR
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        try:
            if os.name == "nt":
                os.startfile(LOG_DIR)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", LOG_DIR])
            else:
                subprocess.Popen(["xdg-open", LOG_DIR])
        except Exception:  # noqa: BLE001
            messagebox.showwarning("Логи", f"Папка логов: {LOG_DIR}")

    def _refresh_logs(self) -> None:
        def load_tail() -> str:
            if LOG_FILE.exists():
                with LOG_FILE.open("r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()[-200:]
                return "".join(lines)
            return "Логи появятся после первого запуска бота."

        content = load_tail()
        self.log_text.delete("1.0", END)
        self.log_text.insert("1.0", content)
        self.root.after(1000, self._refresh_logs)


def main() -> None:
    root = Tk()
    ControlPanel(root)
    root.mainloop()


if __name__ == "__main__":
    main()

