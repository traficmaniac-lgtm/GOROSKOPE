from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Dict, List

from app.config.runtime import runtime_config
from app.config.settings import settings
from app.core.validators import validate_date, validate_time
from app.db.storage import Database
from app.services.ai_service import resolve_ai_service
from app.services.prompt_builder import HoroscopeRequest, build_horoscope_prompt
from app.services.quota_service import QuotaService


@dataclass
class SimulationStep:
    role: str
    text: str


@dataclass
class SimulationState:
    user_id: int = 9999
    mode: str = "Прогноз на сегодня"
    birth_date: str = "01.01.1990"
    birth_time: str | None = "08:00"
    birth_place: str = "Москва"
    gender: str = "gender_f"
    focus: str = "focus_general"
    action: str = "hs_today"
    history: List[SimulationStep] = field(default_factory=list)


class HoroscopeSimulator:
    def __init__(self) -> None:
        self.state = SimulationState()
        self.db = Database(settings.db_path)
        self.ai_service = resolve_ai_service()
        self.quota_service = QuotaService(self.db, free_quota=runtime_config.free_quota)
        self._init_lock = asyncio.Lock()

    async def ensure_ready(self) -> None:
        async with self._init_lock:
            await self.db.init()

    def reset(self) -> None:
        self.state = SimulationState()

    def set_values(self, values: Dict[str, str | None]) -> None:
        for key, value in values.items():
            if hasattr(self.state, key):
                setattr(self.state, key, value)  # type: ignore[arg-type]

    async def simulate(self) -> str:
        await self.ensure_ready()
        await self.quota_service.ensure_user(self.state.user_id)
        free_left = await self.quota_service.get_free_left(self.state.user_id)
        if free_left <= 0:
            return "Квота исчерпана"
        consumed = await self.quota_service.consume_one(self.state.user_id)
        if not consumed:
            return "Квота недоступна"

        if not validate_date(self.state.birth_date):
            return "Некорректная дата"
        if self.state.birth_time and not validate_time(self.state.birth_time):
            return "Некорректное время"

        req = HoroscopeRequest(
            mode=self.state.mode,
            birth_date=self.state.birth_date,
            birth_time=self.state.birth_time,
            birth_place=self.state.birth_place,
            gender=self.state.gender,
            focus=self.state.focus,
        )
        prompt = build_horoscope_prompt(req)
        await self.quota_service.log_request(self.state.user_id, "horoscope", self.state.action, "simulated")
        response = await self.ai_service.generate(prompt)
        self.state.history.append(SimulationStep(role="user", text=str(req.__dict__)))
        self.state.history.append(SimulationStep(role="bot", text=response))
        return response

