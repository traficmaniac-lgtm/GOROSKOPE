from __future__ import annotations

import abc
import logging

from app.config.settings import settings

logger = logging.getLogger(__name__)

try:  # pragma: no cover - optional
    from openai import AsyncOpenAI
except Exception:  # pragma: no cover
    AsyncOpenAI = None


class AIService(abc.ABC):
    @abc.abstractmethod
    async def generate(self, prompt: str) -> str:
        raise NotImplementedError


class StubAIService(AIService):
    async def generate(self, prompt: str) -> str:  # pragma: no cover - stub
        logger.info("Stub AI generation")
        return "Это демонстрационный гороскоп. Настоящий ответ будет сгенерирован после подключения AI."


class OpenAIService(AIService):
    def __init__(self, api_key: str) -> None:
        if AsyncOpenAI is None:
            raise RuntimeError("OpenAI SDK не установлен")
        self.client = AsyncOpenAI(api_key=api_key)

    async def generate(self, prompt: str) -> str:  # pragma: no cover - network call
        completion = await self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600,
        )
        return completion.choices[0].message.content or ""


def resolve_ai_service() -> AIService:
    if settings.use_openai and settings.openai_api_key:
        return OpenAIService(settings.openai_api_key)
    return StubAIService()
