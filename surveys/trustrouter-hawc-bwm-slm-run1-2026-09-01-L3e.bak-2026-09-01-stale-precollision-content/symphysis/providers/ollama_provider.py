"""Local model provider via Ollama's HTTP API. No API key required."""

from __future__ import annotations

import os
from typing import Any, Dict, List

import requests

from .base import ProviderError, ProviderResponse


class OllamaProvider:
    def __init__(self, base_url: str | None = None, default_timeout: float | None = None) -> None:
        self.base_url = base_url or os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        # 900s (15 min), not requests' 300s socket-read default: switching
        # between several distinct models in one survey (as the 6-Ollama-
        # family roster does) makes Ollama cold-load each one from disk on
        # its first request, and a reasoning model (e.g. deepseek-r1) can
        # spend a long time on chain-of-thought before its final answer.
        # Measured hitting the old 300s default in exactly that scenario.
        self.default_timeout = default_timeout or float(os.environ.get("OLLAMA_TIMEOUT_SECONDS", "900"))

    def complete(
        self,
        messages: List[Dict[str, str]],
        *,
        model: str,
        temperature: float,
        max_tokens: int,
        top_p: float = 1.0,
        seed: int | None = None,
        timeout: float | None = None,
        **extra: Any,
    ) -> ProviderResponse:
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "top_p": top_p,
                **({"seed": seed} if seed is not None else {}),
                **extra,
            },
        }
        try:
            resp = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=timeout or self.default_timeout)
            resp.raise_for_status()
        except requests.RequestException as exc:
            raise ProviderError(f"Ollama request failed: {exc}") from exc

        data = resp.json()
        text = data.get("message", {}).get("content", "")
        return ProviderResponse(text=text, raw=data, model=model, finish_reason=data.get("done_reason", ""))
