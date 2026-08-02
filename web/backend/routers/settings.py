"""LLM-endpoint settings: lets the web UI point this app's Ollama calls at a
remote host (e.g. the veritas server, over Tailscale) or back at a local
instance, without editing .env and restarting the backend process.

Previously OLLAMA_BASE_URL was read once from the environment when the
`ollama` provider was first constructed and then cached for the life of the
process (see agentic_survey.providers). That's fine for the CLI (a fresh
process per run) but meant the long-lived web backend could never actually
change endpoint at runtime -- only at process start. This router writes the
new value to os.environ AND drops the cached provider instance
(`providers.reset_provider`) so the very next run picks it up.
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

# Convenience presets surfaced in the UI. The veritas-server address is the
# same Tailscale IP already documented in this repo's README and
# .env.example ("Remote-LLM mode") -- only reachable to devices on that
# private tailnet, not a public address or a credential.
PRESETS = {
    "local": DEFAULT_BASE_URL,
    "veritas-server": "http://100.77.119.21:11434",
}


class LlmSettingsIn(BaseModel):
    ollama_base_url: str
    ollama_timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS

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


def _read_persisted() -> Dict[str, Any]:
    if SETTINGS_PATH.exists():
        try:
            return json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def load_settings_into_env() -> None:
    """Apply any persisted settings to the process environment. Called once
    at backend startup so a chosen endpoint survives a restart."""
    persisted = _read_persisted()
    if "ollama_base_url" in persisted:
        os.environ["OLLAMA_BASE_URL"] = persisted["ollama_base_url"]
    if "ollama_timeout_seconds" in persisted:
        os.environ["OLLAMA_TIMEOUT_SECONDS"] = str(persisted["ollama_timeout_seconds"])


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
    return {
        "ollama_base_url": os.environ.get("OLLAMA_BASE_URL", DEFAULT_BASE_URL),
        "ollama_timeout_seconds": int(os.environ.get("OLLAMA_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS)),
        "presets": PRESETS,
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

    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {"ollama_base_url": body.ollama_base_url, "ollama_timeout_seconds": body.ollama_timeout_seconds}
    SETTINGS_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    os.environ["OLLAMA_BASE_URL"] = body.ollama_base_url
    os.environ["OLLAMA_TIMEOUT_SECONDS"] = str(body.ollama_timeout_seconds)
    providers.reset_provider("ollama")

    return {**payload, "presets": PRESETS}
