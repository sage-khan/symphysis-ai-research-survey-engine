"""Provider interface every LLM backend implements."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Protocol


@dataclass
class ProviderResponse:
    text: str
    raw: Dict[str, Any] = field(default_factory=dict)  # full raw API payload, for audit logs
    model: str = ""
    finish_reason: str = ""


class LLMProvider(Protocol):
    """Every provider takes a chat-style message list and model hyperparameters
    and returns a ProviderResponse. Providers must not embed default prompts,
    temperatures, or model names; those come from AgentConfig."""

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
        ...


class ProviderError(Exception):
    """Raised on any provider-side failure (network, auth, malformed reply)."""
