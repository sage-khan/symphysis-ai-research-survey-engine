"""Runtime settings: where this app's Ollama calls go, and which API keys
its hosted-provider agents (Anthropic, OpenAI, OpenRouter, Groq, Gemini,
xAI) use.

Previously OLLAMA_BASE_URL was read once from the environment when the
`ollama` provider was first constructed and then cached for the life of the
process (see agentic_survey.providers). That's fine for the CLI (a fresh
process per run) but meant the long-lived web backend could never actually
change endpoint at runtime -- only at process start. This router writes the
new value to os.environ AND drops the cached provider instance
(`providers.reset_provider`) so the very next run picks it up. The same
pattern applies to API keys: setting one here writes it to os.environ and
drops that provider's cached instance.

Nothing here is specific to any one deployment -- there is no hardcoded
remote-server address. "Local" is the only built-in preset; anyone can save
their own named remote endpoint (their own machine, a lab server, whatever)
under any label they choose, and it persists across restarts.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator

from ..paths import REPO_ROOT

router = APIRouter(prefix="/api/settings", tags=["settings"])

SETTINGS_PATH = REPO_ROOT / "web" / "backend" / "data" / "llm_settings.json"
DEFAULT_BASE_URL = "http://localhost:11434"
DEFAULT_TIMEOUT_SECONDS = 900

BUILTIN_PRESETS = {"local": DEFAULT_BASE_URL}

# provider key -> the environment variable its provider class reads (see
# providers/anthropic_provider.py, providers/openai_compatible.py).
API_KEY_ENV_VARS = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "groq": "GROQ_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "xai": "XAI_API_KEY",
}


class LlmSettingsIn(BaseModel):
    ollama_base_url: str
    ollama_timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS
    save_preset_label: Optional[str] = None  # if set, also saves ollama_base_url under this name

    @field_validator("ollama_base_url")
    @classmethod
    def _valid_url(cls, v: str) -> str:
        v = v.strip().rstrip("/")
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("ollama_base_url must start with http:// or https://")
        return v

    @field_validator("ollama_timeout_seconds")
    @classmethod
    def _positive_timeout(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("ollama_timeout_seconds must be positive")
        return v


class ApiKeysIn(BaseModel):
    """Only keys actually present in the body are changed; omit a provider
    to leave its stored key untouched. An empty string clears it."""

    anthropic: Optional[str] = None
    openai: Optional[str] = None
    openrouter: Optional[str] = None
    groq: Optional[str] = None
    gemini: Optional[str] = None
    xai: Optional[str] = None


def _read_persisted() -> Dict[str, Any]:
    if SETTINGS_PATH.exists():
        try:
            return json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _write_persisted(data: Dict[str, Any]) -> None:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def load_settings_into_env() -> None:
    """Apply any persisted settings (Ollama endpoint + API keys) to the
    process environment. Called once at backend startup so they survive a
    restart without needing to be re-entered."""
    persisted = _read_persisted()
    if "ollama_base_url" in persisted:
        os.environ["OLLAMA_BASE_URL"] = persisted["ollama_base_url"]
    if "ollama_timeout_seconds" in persisted:
        os.environ["OLLAMA_TIMEOUT_SECONDS"] = str(persisted["ollama_timeout_seconds"])
    for provider, key in (persisted.get("api_keys") or {}).items():
        env_var = API_KEY_ENV_VARS.get(provider)
        if env_var and key:
            os.environ[env_var] = key


def _ping(base_url: str, timeout: float = 5.0) -> Dict[str, Any]:
    try:
        resp = requests.get(f"{base_url.rstrip('/')}/api/tags", timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        return {"reachable": True, "models": sorted(m["name"] for m in data.get("models", []))}
    except requests.RequestException as exc:
        return {"reachable": False, "error": str(exc)}


@router.get("/llm")
def get_llm_settings() -> Dict[str, Any]:
    persisted = _read_persisted()
    presets = {**BUILTIN_PRESETS, **(persisted.get("custom_presets") or {})}
    return {
        "ollama_base_url": os.environ.get("OLLAMA_BASE_URL", DEFAULT_BASE_URL),
        "ollama_timeout_seconds": int(os.environ.get("OLLAMA_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS)),
        "presets": presets,
    }


@router.get("/llm/test")
def test_llm_endpoint(base_url: Optional[str] = None) -> Dict[str, Any]:
    """Ping a candidate endpoint (or the currently configured one, if
    base_url is omitted) without saving anything -- lets the UI verify
    reachability before committing to a setting."""
    url = (base_url or os.environ.get("OLLAMA_BASE_URL", DEFAULT_BASE_URL)).strip().rstrip("/")
    if not (url.startswith("http://") or url.startswith("https://")):
        raise HTTPException(400, "base_url must start with http:// or https://")
    result = _ping(url)
    result["base_url"] = url
    return result


@router.put("/llm")
def set_llm_settings(body: LlmSettingsIn) -> Dict[str, Any]:
    from agentic_survey import providers

    persisted = _read_persisted()
    persisted["ollama_base_url"] = body.ollama_base_url
    persisted["ollama_timeout_seconds"] = body.ollama_timeout_seconds
    if body.save_preset_label:
        label = body.save_preset_label.strip()
        if label and label != "local":
            custom = persisted.setdefault("custom_presets", {})
            custom[label] = body.ollama_base_url
    _write_persisted(persisted)

    os.environ["OLLAMA_BASE_URL"] = body.ollama_base_url
    os.environ["OLLAMA_TIMEOUT_SECONDS"] = str(body.ollama_timeout_seconds)
    providers.reset_provider("ollama")

    presets = {**BUILTIN_PRESETS, **(persisted.get("custom_presets") or {})}
    return {
        "ollama_base_url": body.ollama_base_url,
        "ollama_timeout_seconds": body.ollama_timeout_seconds,
        "presets": presets,
    }


@router.delete("/llm/presets/{label}")
def delete_preset(label: str) -> Dict[str, Any]:
    if label in BUILTIN_PRESETS:
        raise HTTPException(400, f"'{label}' is a built-in preset and cannot be deleted.")
    persisted = _read_persisted()
    custom = persisted.get("custom_presets") or {}
    if label not in custom:
        raise HTTPException(404, f"No saved preset named '{label}'.")
    del custom[label]
    persisted["custom_presets"] = custom
    _write_persisted(persisted)
    return {**BUILTIN_PRESETS, **custom}


@router.get("/api-keys")
def get_api_key_status() -> Dict[str, bool]:
    """Never returns the actual key values, only whether each provider
    currently has one configured (persisted or set directly in the process
    environment) -- so the UI can show a check mark, not the secret."""
    persisted = _read_persisted().get("api_keys") or {}
    return {
        provider: bool(persisted.get(provider) or os.environ.get(env_var))
        for provider, env_var in API_KEY_ENV_VARS.items()
    }


@router.put("/api-keys")
def set_api_keys(body: ApiKeysIn) -> Dict[str, bool]:
    from agentic_survey import providers

    persisted = _read_persisted()
    stored = persisted.setdefault("api_keys", {})
    for provider, env_var in API_KEY_ENV_VARS.items():
        value = getattr(body, provider)
        if value is None:
            continue  # omitted: leave untouched
        stored[provider] = value
        if value:
            os.environ[env_var] = value
        else:
            os.environ.pop(env_var, None)
        providers.reset_provider(provider)
    _write_persisted(persisted)
    return get_api_key_status()
