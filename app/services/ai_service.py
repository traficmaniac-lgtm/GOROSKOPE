from __future__ import annotations

import abc
import asyncio
import logging
import socket
from dataclasses import dataclass

from app.config.settings import settings
from app.services.prompt_builder import BuiltPrompt

logger = logging.getLogger(__name__)

try:  # pragma: no cover - optional
    from openai import AsyncOpenAI
    from openai import BadRequestError
    from openai._exceptions import APIError, AuthenticationError, RateLimitError
except Exception:  # pragma: no cover
    AsyncOpenAI = None
    BadRequestError = AuthenticationError = APIError = RateLimitError = None


class AIService(abc.ABC):
    @abc.abstractmethod
    async def generate(self, prompt: BuiltPrompt) -> str:
        raise NotImplementedError

    async def healthcheck(self) -> str:
        """Optional quick health-check."""
        prompt = BuiltPrompt(
            system_prompt="Ping", user_prompt="Ответь одним словом 'ok'"
        )
        return await self.generate(prompt)


class AIServiceError(RuntimeError):
    pass


class StubAIService(AIService):
    async def generate(self, prompt: BuiltPrompt) -> str:  # pragma: no cover - stub
        logger.info("Stub AI generation (offline mode)")
        return "Режим STUB: это демо-гороскоп. Подключите OpenAI, чтобы получить реальный прогноз."


class OpenAIService(AIService):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        if AsyncOpenAI is None:
            raise RuntimeError("OpenAI SDK не установлен")
        self.client = AsyncOpenAI(api_key=api_key, timeout=30.0, max_retries=2)
        self.model = model

    async def _call_completion(self, prompt: BuiltPrompt) -> str:
        completion = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": prompt.system_prompt},
                {"role": "user", "content": prompt.user_prompt},
            ],
            max_tokens=700,
            temperature=0.7,
        )
        return completion.choices[0].message.content or ""

    async def generate(self, prompt: BuiltPrompt) -> str:  # pragma: no cover - network call
        try:
            return await asyncio.wait_for(self._call_completion(prompt), timeout=40.0)
        except asyncio.TimeoutError as exc:
            logger.exception("OpenAI request timeout")
            raise AIServiceError("Timeout при обращении к OpenAI") from exc
        except AuthenticationError as exc:  # type: ignore[misc]
            logger.exception("OpenAI authentication error")
            raise AIServiceError("Проверьте OPENAI_API_KEY: доступ запрещен") from exc
        except RateLimitError as exc:  # type: ignore[misc]
            logger.exception("OpenAI rate limit")
            raise AIServiceError("OpenAI вернул 429 (лимиты). Попробуйте позже") from exc
        except APIError as exc:  # type: ignore[misc]
            logger.exception("OpenAI server error")
            raise AIServiceError("Сервер OpenAI недоступен, попробуйте позже") from exc
        except BadRequestError as exc:  # type: ignore[misc]
            logger.exception("OpenAI bad request: %s", exc)
            raise AIServiceError("Некорректный запрос в OpenAI") from exc
        except Exception as exc:  # pragma: no cover - unexpected
            logger.exception("OpenAI request failed: %s", exc)
            raise AIServiceError("Не удалось получить ответ от OpenAI") from exc


@dataclass(slots=True)
class AIResolution:
    service: AIService
    mode: str


def resolve_ai_service() -> AIResolution:
    if settings.use_openai:
        if settings.openai_api_key:
            logger.info("AI mode: OpenAI (%s)", "gpt-4o-mini")
            return AIResolution(OpenAIService(settings.openai_api_key), mode="openai")
        logger.warning("USE_OPENAI=true, но OPENAI_API_KEY не задан. Переключаюсь на STUB.")
    logger.info("AI mode: STUB")
    return AIResolution(StubAIService(), mode="stub")


def check_network_host(host: str, port: int, timeout: float = 3.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False
