"""Simple Tkinter UI for editing .env and testing connectivity."""
from __future__ import annotations

import os
import subprocess
import sys
import threading
from pathlib import Path
from tkinter import BOTH, DISABLED, END, NORMAL, Button, Entry, Frame, Label, Text, Tk, messagebox

from app.openai_client import OpenAIClient

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"
DEFAULT_MODEL = "gpt-4o-mini"


class SettingsApp:
    def __init__(self, root: Tk) -> None:
        self.root = root
        self.root.title("GOROSKOPE Setup")
        self.bot_process: subprocess.Popen | None = None

        self.fields = {
            "TELEGRAM_BOT_TOKEN": None,
            "OPENAI_API_KEY": None,
            "OPENAI_MODEL": None,
            "ADMIN_TELEGRAM_ID": None,
        }

        self._build_form()
        self._build_buttons()
        self._build_log()
        self._load_env_values()

    def _build_form(self) -> None:
        form = Frame(self.root)
        form.pack(fill=BOTH, padx=10, pady=10)

        self.fields["TELEGRAM_BOT_TOKEN"] = self._add_field(form, "TELEGRAM_BOT_TOKEN")
        self.fields["OPENAI_API_KEY"] = self._add_field(form, "OPENAI_API_KEY")
        self.fields["OPENAI_MODEL"] = self._add_field(form, "OPENAI_MODEL", DEFAULT_MODEL)
        self.fields["ADMIN_TELEGRAM_ID"] = self._add_field(form, "ADMIN_TELEGRAM_ID")

    def _build_buttons(self) -> None:
        buttons = Frame(self.root)
        buttons.pack(fill=BOTH, padx=10, pady=(0, 5))

        Button(buttons, text="Save", command=self.save_env).pack(side="left", padx=5)
        Button(buttons, text="Test OpenAI", command=self.test_openai).pack(side="left", padx=5)
        Button(buttons, text="Run Bot", command=self.run_bot).pack(side="left", padx=5)
        Button(buttons, text="Stop Bot", command=self.stop_bot).pack(side="left", padx=5)

    def _build_log(self) -> None:
        Label(self.root, text="Log").pack(anchor="w", padx=10)
        self.log_box = Text(self.root, height=12, state=DISABLED)
        self.log_box.pack(fill=BOTH, expand=True, padx=10, pady=(0, 10))

    def _add_field(self, parent: Frame, label: str, default: str = "") -> Entry:
        row = Frame(parent)
        row.pack(fill=BOTH, pady=3)
        Label(row, text=label, width=20, anchor="w").pack(side="left")
        entry = Entry(row, width=50)
        entry.pack(side="left", fill=BOTH, expand=True)
        if default:
            entry.insert(0, default)
        return entry

    def _load_env_values(self) -> None:
        if ENV_FILE.exists():
            with ENV_FILE.open("r", encoding="utf-8") as f:
                for line in f:
                    if "=" in line:
                        key, value = line.strip().split("=", 1)
                        if key in self.fields and value:
                            self.fields[key].delete(0, END)
                            self.fields[key].insert(0, value)
            self._log("Настройки .env загружены.")
        else:
            self._log("Файл .env не найден. Заполните поля и нажмите Save.")

    def _log(self, message: str) -> None:
        self.log_box.configure(state=NORMAL)
        self.log_box.insert(END, f"{message}\n")
        self.log_box.configure(state=DISABLED)
        self.log_box.see(END)

    def save_env(self) -> None:
        values = {key: (field.get().strip() if field else "") for key, field in self.fields.items()}
        if not values.get("OPENAI_MODEL"):
            values["OPENAI_MODEL"] = DEFAULT_MODEL

        content = (
            f"TELEGRAM_BOT_TOKEN={values['TELEGRAM_BOT_TOKEN']}\n"
            f"OPENAI_API_KEY={values['OPENAI_API_KEY']}\n"
            f"OPENAI_MODEL={values['OPENAI_MODEL']}\n"
            f"ADMIN_TELEGRAM_ID={values['ADMIN_TELEGRAM_ID']}\n"
            f"TIMEZONE=Europe/Kyiv\n"
        )

        with ENV_FILE.open("w", encoding="utf-8") as f:
            f.write(content)

        DATA_DIR = BASE_DIR / "data"
        DATA_DIR.mkdir(parents=True, exist_ok=True)

        self._log(".env сохранён.")
        messagebox.showinfo("Сохранено", ".env обновлён.")

    def _build_openai_client(self) -> OpenAIClient | None:
        api_key = self.fields["OPENAI_API_KEY"].get().strip()
        model = self.fields["OPENAI_MODEL"].get().strip() or DEFAULT_MODEL
        if not api_key:
            messagebox.showwarning("OpenAI", "Заполните OPENAI_API_KEY и сохраните настройки.")
            return None
        return OpenAIClient(api_key, model)

    def test_openai(self) -> None:
        client = self._build_openai_client()
        if not client:
            return

        def worker() -> None:
            try:
                reply = client.test_greeting()
                self.root.after(0, lambda: self._log(f"OpenAI: {reply}"))
            except Exception as exc:  # noqa: BLE001
                self.root.after(0, lambda: self._log(f"Ошибка OpenAI: {exc}"))

        threading.Thread(target=worker, daemon=True).start()
        self._log("Отправлен тестовый запрос в OpenAI...")

    def run_bot(self) -> None:
        if self.bot_process and self.bot_process.poll() is None:
            messagebox.showinfo("Бот", "Бот уже запущен.")
            return

        command = ["cmd", "/c", "run_bot.bat"] if os.name == "nt" else [sys.executable, "-m", "app.bot"]
        try:
            self.bot_process = subprocess.Popen(command, cwd=BASE_DIR)
            self._log("Бот запущен.")
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Ошибка", f"Не удалось запустить бота: {exc}")
            self._log(f"Не удалось запустить бота: {exc}")

    def stop_bot(self) -> None:
        if self.bot_process and self.bot_process.poll() is None:
            self.bot_process.terminate()
            self.bot_process.wait(timeout=5)
            self._log("Бот остановлен.")
        else:
            self._log("Бот не запущен.")


def main() -> None:
    root = Tk()
    app = SettingsApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
