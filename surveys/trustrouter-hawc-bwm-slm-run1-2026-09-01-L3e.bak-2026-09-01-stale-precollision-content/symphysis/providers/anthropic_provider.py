"""Anthropic Claude provider. Requires ANTHROPIC_API_KEY in the environment."""

from __future__ import annotations

import os
from typing import Any, Dict, List

from .base import ProviderError, ProviderResponse

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:  # pragma: no cover - import-time only
    ANTHROPIC_AVAILABLE = False


class AnthropicProvider:
    def __init__(self, api_key: str | None = None) -> None:
        if not ANTHROPIC_AVAILABLE:
            raise ProviderError("anthropic package is not installed")
        key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise ProviderError("ANTHROPIC_API_KEY is not set")
        self.client = anthropic.Anthropic(api_key=key)

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
        system = "\n".join(m["content"] for m in messages if m["role"] == "system")
        user_turns = [m for m in messages if m["role"] != "system"]
        try:
            resp = self.client.messages.create(
                model=model,
                system=system or None,
                messages=user_turns,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                **extra,
            )
        except Exception as exc:  # anthropic raises its own exception hierarchy
            raise ProviderError(f"Anthropic request failed: {exc}") from exc

        text = "".join(block.text for block in resp.content if getattr(block, "type", "") == "text")
        return ProviderResponse(
            text=text,
            raw=resp.model_dump() if hasattr(resp, "model_dump") else {},
            model=model,
            finish_reason=resp.stop_reason or "",
        )
