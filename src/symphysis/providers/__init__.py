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
    from .claude_cli_provider import ClaudeCliProvider
    from .openai_compatible import GeminiProvider, GroqProvider, OpenAIProvider, OpenRouterProvider, XaiProvider
    from .manual_provider import ManualProvider

    _REGISTRY.update(
        {
            "ollama": OllamaProvider,
            "anthropic": AnthropicProvider,
            "claude_cli": ClaudeCliProvider,
            "openai": OpenAIProvider,
            "openrouter": OpenRouterProvider,
            "groq": GroqProvider,
            "gemini": GeminiProvider,
            "xai": XaiProvider,
            "manual": ManualProvider,
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


def reset_provider(name: str) -> None:
    """Drop a cached provider instance so the next get_provider(name) call
    re-reads its config (e.g. OLLAMA_BASE_URL) from the environment instead
    of reusing whatever was current the first time it was constructed.
    Needed because a long-lived process (the web backend) would otherwise
    never see an LLM-endpoint setting changed after its first survey run."""
    _INSTANCES.pop(name, None)


__all__ = ["LLMProvider", "ProviderError", "ProviderResponse", "get_provider", "reset_provider"]
