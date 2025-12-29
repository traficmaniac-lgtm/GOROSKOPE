from __future__ import annotations

import re
from pathlib import Path
from typing import Dict

from app.config.settings import Settings


ENV_PATTERN = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$")


class EnvManager:
    def __init__(self, path: str = ".env") -> None:
        self.path = Path(path)

    def read_raw_lines(self) -> list[str]:
        if not self.path.exists():
            return []
        return self.path.read_text(encoding="utf-8").splitlines()

    def create_from_example(self, example_path: Path | str = ".env.example") -> bool:
        example = Path(example_path)
        if not example.exists():
            return False
        self.path.write_text(example.read_text(encoding="utf-8"), encoding="utf-8")
        return True

    def ensure_exists(self) -> None:
        if not self.path.exists():
            self.path.touch()

    def load(self) -> Dict[str, str]:
        env: Dict[str, str] = {}
        for line in self.read_raw_lines():
            match = ENV_PATTERN.match(line)
            if match:
                env[match.group(1)] = match.group(2)
        return env

    def save(self, updates: Dict[str, str]) -> None:
        lines = self.read_raw_lines()
        seen = set()
        new_lines: list[str] = []
        for line in lines:
            match = ENV_PATTERN.match(line)
            if match:
                key = match.group(1)
                if key in updates:
                    new_lines.append(f"{key}={updates[key]}")
                    seen.add(key)
                else:
                    new_lines.append(line)
                    seen.add(key)
            else:
                new_lines.append(line)

        for key, value in updates.items():
            if key not in seen:
                new_lines.append(f"{key}={value}")

        self.path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

    def validate(self, env: Dict[str, str]) -> list[str]:
        errors: list[str] = []
        if not env.get("BOT_TOKEN"):
            errors.append("BOT_TOKEN не задан")
        if env.get("USE_OPENAI", "false").lower() == "true" and not env.get("OPENAI_API_KEY"):
            errors.append("USE_OPENAI=true, но OPENAI_API_KEY пуст")
        return errors

    def masked_env(self, env: Dict[str, str]) -> Dict[str, str]:
        masked: Dict[str, str] = {}
        for key, value in env.items():
            if key.endswith("TOKEN") or key.endswith("KEY"):
                if len(value) > 8:
                    masked[key] = f"{value[:4]}...{value[-4:]}"
                else:
                    masked[key] = "***" if value else ""
            else:
                masked[key] = value
        return masked

    def load_settings(self) -> Settings:
        env_data = self.load()
        return Settings(**{k.lower(): v for k, v in env_data.items()})

