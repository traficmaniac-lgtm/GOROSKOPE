import logging
import os
import subprocess
import sys
from pathlib import Path
import tkinter as tk
from tkinter import messagebox

logger = logging.getLogger("launcher")


def copy_text(root: tk.Tk, text: str) -> None:
    try:
        root.clipboard_clear()
        root.clipboard_append(text)
        logger.info("Копирование в буфер выполнено (%d символов)", len(text))
    except Exception as exc:  # pragma: no cover - runtime guard
        logger.exception("Не удалось скопировать текст: %s", exc)
        messagebox.showerror("Копирование", f"Не удалось скопировать: {exc}")
        return


def paste_text(root: tk.Tk) -> str:
    try:
        data = root.clipboard_get()
        logger.info("Вставка из буфера выполнена (%d символов)", len(data))
        return data
    except Exception as exc:  # pragma: no cover - runtime guard
        logger.exception("Не удалось вставить текст: %s", exc)
        messagebox.showerror("Вставка", f"Не удалось вставить: {exc}")
        return ""


def bind_clipboard_shortcuts(widget: tk.Widget) -> None:
    def select_all(event: tk.Event) -> str:
        try:
            if isinstance(widget, tk.Text):
                widget.tag_add("sel", "1.0", "end-1c")
            else:
                widget.select_range(0, tk.END)
            return "break"
        except Exception:
            return "break"

    def copy(event: tk.Event) -> str:
        try:
            widget.event_generate("<<Copy>>")
        except Exception:
            pass
        return "break"

    def paste(event: tk.Event) -> str:
        try:
            widget.event_generate("<<Paste>>")
        except Exception:
            pass
        return "break"

    def cut(event: tk.Event) -> str:
        try:
            widget.event_generate("<<Cut>>")
        except Exception:
            pass
        return "break"

    widget.bind("<Control-a>", select_all)
    widget.bind("<Control-A>", select_all)
    widget.bind("<Control-c>", copy)
    widget.bind("<Control-C>", copy)
    widget.bind("<Control-v>", paste)
    widget.bind("<Control-V>", paste)
    widget.bind("<Control-x>", cut)
    widget.bind("<Control-X>", cut)


def open_path(path: Path) -> bool:
    try:
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(path)
        if sys.platform.startswith("win"):
            if path.is_dir():
                os.startfile(path)  # type: ignore[attr-defined]
            else:
                os.startfile(path.resolve())  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", "-R" if path.is_file() else "-a", "Finder", str(path)])
        else:
            if path.is_file():
                subprocess.Popen(["xdg-open", str(path.parent)])
            else:
                subprocess.Popen(["xdg-open", str(path)])
        logger.info("Открыт путь в проводнике: %s", path)
        return True
    except Exception as exc:  # pragma: no cover - runtime guard
        logger.exception("Не удалось открыть путь %s: %s", path, exc)
        messagebox.showerror("Открытие", f"Не удалось открыть {path}: {exc}")
        return False


def set_status(var: tk.StringVar, msg: str) -> None:
    var.set(msg)
    logger.info(msg)
