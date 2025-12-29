from __future__ import annotations

import logging
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Callable

from app.core.logging import LOG_FILE
from app.tools.env_manager import EnvManager
from app.services.health import validate_token_value


logger = logging.getLogger(__name__)


class BotRunner:
    def __init__(self, log_file: Path | str | None = None) -> None:
        self.process: subprocess.Popen[bytes] | None = None
        self.log_file = Path(log_file) if log_file else LOG_FILE
        self._stop_event = threading.Event()
        self._log_thread: threading.Thread | None = None

    def start(self) -> None:
        if self.process and self.process.poll() is None:
            raise RuntimeError("Бот уже запущен")

        env_manager = EnvManager()
        env = env_manager.load()
        errors = env_manager.validate(env)
        if errors:
            raise RuntimeError("; ".join(errors))
        validate_token_value(env.get("BOT_TOKEN", ""))

        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.log_file.touch(exist_ok=True)
        try:
            self.process = subprocess.Popen(
                [sys.executable, "bot.py"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT
            )
        except Exception as exc:  # pragma: no cover - runtime guard
            logger.exception("Failed to start bot: %s", exc)
            raise
        self._stop_event.clear()

    def stop(self) -> None:
        if not self.process:
            return
        self.process.terminate()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()
        self.process = None

    def tail_logs(self, callback: Callable[[str], None], interval: float = 1.0) -> None:
        def _run() -> None:
            last_size = 0
            while not self._stop_event.is_set():
                if self.log_file.exists():
                    size = self.log_file.stat().st_size
                    if size != last_size:
                        content = self.log_file.read_text(encoding="utf-8", errors="ignore")
                        callback(content)
                        last_size = size
                time.sleep(interval)

        if self._log_thread and self._log_thread.is_alive():
            return
        self._log_thread = threading.Thread(target=_run, daemon=True)
        self._log_thread.start()

