from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from app.config.settings import settings


class EditorStore:
    def __init__(self, path: str | None = None) -> None:
        self.path = Path(path or settings.overrides_path)

    def load(self) -> Dict[str, Any]:
        if not self.path.exists():
            return {}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:  # pragma: no cover - runtime guard
            return {}

    def save(self, data: Dict[str, Any]) -> None:
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

