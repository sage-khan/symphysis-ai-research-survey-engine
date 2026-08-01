"""Shared implementation for OpenAI and OpenAI-compatible APIs (OpenRouter).

Both providers speak the same chat-completions wire format; only the base
URL and the API-key environment variable differ, so one class parameterised
by those two things covers both rather than duplicating the request logic.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List

from .base import ProviderError, ProviderResponse

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:  # pragma: no cover - import-time only
    OPENAI_AVAILABLE = False


class OpenAICompatibleProvider:
    def __init__(self, api_key_env: str, base_url: str | None = None, api_key: str | None = None) -> None:
        if not OPENAI_AVAILABLE:
            raise ProviderError("openai package is not installed")
        key = api_key or os.environ.get(api_key_env)
        if not key:
            raise ProviderError(f"{api_key_env} is not set")
        self.client = openai.OpenAI(api_key=key, base_url=base_url)

    def complete(
        self,
        messages: List[Dict[str, str]],
        *,
        model: str,
        temperature: float,
        max_tokens: int,
        top_p: float = 1.0,
        seed: int | None = None,
        **extra: Any,
    ) -> ProviderResponse:
        try:
            resp = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                seed=seed,
                **extra,
            )
        except Exception as exc:
            raise ProviderError(f"{self.__class__.__name__} request failed: {exc}") from exc

        choice = resp.choices[0]
        return ProviderResponse(
            text=choice.message.content or "",
            raw=resp.model_dump() if hasattr(resp, "model_dump") else {},
            model=model,
            finish_reason=choice.finish_reason or "",
        )


class OpenAIProvider(OpenAICompatibleProvider):
    def __init__(self, api_key: str | None = None) -> None:
        super().__init__(api_key_env="OPENAI_API_KEY", base_url=None, api_key=api_key)


class OpenRouterProvider(OpenAICompatibleProvider):
    def __init__(self, api_key: str | None = None) -> None:
        super().__init__(
            api_key_env="OPENROUTER_API_KEY",
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
