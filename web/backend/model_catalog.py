"""Live model catalogs, per provider.

The single source of truth for "what models can this provider actually
serve right now": Ollama's own `/api/tags`, or each hosted provider's own
list-models API (OpenAI-compatible providers all expose `GET {base}/models`;
Anthropic has its own `GET /v1/models`). Never a hardcoded list, never an
LLM's guess: every model picker in the UI and the natural-language agent
proposer's hallucinated-model check both read through `list_models()`, so a
model name is only ever treated as real because it was actually seen coming
back from that provider, not because it looked plausible.

`provider: "manual"` (paste-in models with no API, e.g. a web chat UI) has
no list to fetch by definition, so callers should skip validation for it
rather than calling `list_models("manual")`.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List

import requests

_TIMEOUT = 8.0

_API_KEY_ENV = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "groq": "GROQ_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "xai": "XAI_API_KEY",
}

_DEFAULT_BASE_URLS = {
    "openai": "https://api.openai.com/v1",
    "openrouter": "https://openrouter.ai/api/v1",
    "groq": "https://api.groq.com/openai/v1",
    "gemini": "https://generativelanguage.googleapis.com/v1beta/openai",
    "xai": "https://api.x.ai/v1",
}


def _ollama_models(base_url: str) -> List[str]:
    resp = requests.get(f"{base_url.rstrip('/')}/api/tags", timeout=_TIMEOUT)
    resp.raise_for_status()
    return sorted(m["name"] for m in resp.json().get("models", []))


def _openai_compatible_models(base_url: str, api_key: str) -> List[str]:
    resp = requests.get(
        f"{base_url.rstrip('/')}/models",
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    return sorted(m["id"] for m in resp.json().get("data", []))


def _anthropic_models(api_key: str) -> List[str]:
    resp = requests.get(
        "https://api.anthropic.com/v1/models",
        headers={"x-api-key": api_key, "anthropic-version": "2023-06-01"},
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    return sorted(m["id"] for m in resp.json().get("data", []))


def list_models(provider: str) -> Dict[str, Any]:
    """Never raises: an unreachable/uncredentialed provider degrades to
    {"models": [], "error": "..."} (so callers can fall back to a manual
    text field with a visible reason) rather than crashing a page that's
    just trying to populate a dropdown."""
    try:
        if provider == "ollama":
            base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
            return {"models": _ollama_models(base_url), "error": None}

        if provider == "anthropic":
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                return {"models": [], "error": "ANTHROPIC_API_KEY is not set"}
            return {"models": _anthropic_models(api_key), "error": None}

        if provider in _API_KEY_ENV:
            api_key = os.environ.get(_API_KEY_ENV[provider])
            if not api_key:
                return {"models": [], "error": f"{_API_KEY_ENV[provider]} is not set"}
            from agentic_survey import app_config

            base_url = app_config.provider_base_url(provider) or _DEFAULT_BASE_URLS.get(provider)
            return {"models": _openai_compatible_models(base_url, api_key), "error": None}

        if provider == "manual":
            return {"models": [], "error": "provider: manual has no API model list; any label is valid"}

        return {"models": [], "error": f"Unknown provider '{provider}'"}
    except requests.RequestException as exc:
        return {"models": [], "error": str(exc)}


def model_is_available(provider: str, model_name: str) -> bool:
    """True if `model_name` is confirmed present in `provider`'s live
    catalog. If the catalog can't be fetched at all (unreachable, no key),
    returns True: absence of evidence isn't evidence of a hallucination,
    and this should never block on a check that couldn't run. Only used to
    flag likely hallucinations for human review, never to silently reject
    anything."""
    catalog = list_models(provider)
    if catalog["error"] is not None:
        return True
    return model_name in catalog["models"]
