"""Simple AI service wrapper for structured prompts."""
from __future__ import annotations

import logging
import time
from typing import Any, Dict, Tuple

logger = logging.getLogger(__name__)


def build_prompt(payload: Dict[str, Any]) -> str:
    mode = payload.get("mode", "")
    subtype = payload.get("subtype", "")
    style = payload.get("style", "short")
    locale = payload.get("locale", "ru")
    input_block = payload.get("input", {})
    lines = [
        f"Mode: {mode}",
        f"Subtype: {subtype}",
        f"Locale: {locale}",
        f"Style: {style}",
        "Input:"
    ]
    for key, val in input_block.items():
        lines.append(f"- {key}: {val}")
    return "\n".join(lines)


def fake_model_answer(prompt: str) -> Tuple[str, Tuple[int, int]]:
    tokens_in = len(prompt) // 4
    body_lines = [
        "✨ Прогноз готов!",
        "• Ключевые акценты дня",
        "• Практичный совет",
        "• Шаг, который приблизит цель",
    ]
    text = "\n".join(body_lines)
    tokens_out = len(text) // 4
    return text, (tokens_in, tokens_out)


def generate_forecast(payload: Dict[str, Any]) -> Dict[str, Any]:
    prompt = build_prompt(payload)
    answer, tokens = fake_model_answer(prompt)
    return {
        "prompt": prompt,
        "answer": answer,
        "tokens_in": tokens[0],
        "tokens_out": tokens[1],
    }


def run_ai_task(user_id: int, task_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    start = time.time()
    result = generate_forecast(payload)
    latency = time.time() - start
    logger.info(
        "AI task finished",
        extra={
            "user_id": user_id,
            "task_type": task_type,
            "tokens_in": result.get("tokens_in", 0),
            "tokens_out": result.get("tokens_out", 0),
            "latency": latency,
        },
    )
    result["latency"] = latency
    return result

