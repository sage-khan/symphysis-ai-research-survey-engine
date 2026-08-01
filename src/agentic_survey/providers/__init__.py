"""Provider registry: maps a config's `provider:` string to an implementation."""

from __future__ import annotations

from typing import Dict

from .base import LLMProvider, ProviderError, ProviderResponse

_REGISTRY: Dict[str, type] = {}


def _lazy_registry() -> Dict[str, type]:
    if _REGISTRY:
        return _REGISTRY
    from .ollama_provider import OllamaProvider
    from .anthropic_provider import AnthropicProvider
    from .openai_compatible import OpenAIProvider, OpenRouterProvider

    _REGISTRY.update(
        {
            "ollama": OllamaProvider,
            "anthropic": AnthropicProvider,
            "openai": OpenAIProvider,
            "openrouter": OpenRouterProvider,
        }
    )
    return _REGISTRY


_INSTANCES: Dict[str, LLMProvider] = {}


def get_provider(name: str) -> LLMProvider:
    """Return a cached provider instance for `name` (config's provider: key)."""
    if name not in _INSTANCES:
        registry = _lazy_registry()
        if name not in registry:
            raise ProviderError(f"Unknown provider '{name}'. Known: {sorted(registry)}")
        _INSTANCES[name] = registry[name]()
    return _INSTANCES[name]


__all__ = ["LLMProvider", "ProviderError", "ProviderResponse", "get_provider"]
