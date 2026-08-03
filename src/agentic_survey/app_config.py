"""Central, overridable configuration.

Provider base URLs, default model/sampling/RAG hyperparameters, and the
guardrail denylist previously lived as hardcoded literals duplicated across
several files (agent_card.py's dataclass defaults, web/backend/routers/
agents.py's Pydantic defaults, and the frontend's AgentForm.jsx). This
module is the one place that owns them.

`config/defaults.yaml` ships the versioned baseline (checked into git).
`web/backend/data/config_overrides.json` (gitignored, machine-specific) is
an optional partial override merged on top at read time; defaults.yaml
itself is never written to at runtime. Both the CLI and the web backend
read through `get_config()`, never the raw files directly.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULTS_PATH = _REPO_ROOT / "config" / "defaults.yaml"
OVERRIDES_PATH = _REPO_ROOT / "web" / "backend" / "data" / "config_overrides.json"


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_defaults() -> Dict[str, Any]:
    if not DEFAULTS_PATH.exists():
        return {}
    return yaml.safe_load(DEFAULTS_PATH.read_text(encoding="utf-8")) or {}


def load_overrides() -> Dict[str, Any]:
    if OVERRIDES_PATH.exists():
        try:
            return json.loads(OVERRIDES_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def get_config() -> Dict[str, Any]:
    """The effective, merged config: defaults.yaml with any persisted
    override applied on top. Re-reads both files every call (cheap, small
    files) so a change made via the Settings UI takes effect on the very
    next call, no process restart or cache to invalidate."""
    return _deep_merge(load_defaults(), load_overrides())


def save_overrides(partial: Dict[str, Any]) -> Dict[str, Any]:
    """Merge `partial` into the persisted override file (deep merge, so
    setting one provider's base_url doesn't clobber the others) and return
    the new effective config."""
    current = load_overrides()
    merged_overrides = _deep_merge(current, partial)
    OVERRIDES_PATH.parent.mkdir(parents=True, exist_ok=True)
    OVERRIDES_PATH.write_text(json.dumps(merged_overrides, indent=2) + "\n", encoding="utf-8")
    return get_config()


def provider_base_url(provider: str) -> Optional[str]:
    return get_config().get("provider_base_urls", {}).get(provider)


def model_defaults() -> Dict[str, Any]:
    return get_config().get("model_defaults", {})


def sampling_defaults() -> Dict[str, Any]:
    return get_config().get("sampling_defaults", {})


def rag_defaults() -> Dict[str, Any]:
    return get_config().get("rag_defaults", {})


def guardrail_default_denylist() -> list:
    return list(get_config().get("guardrail_default_denylist", []))
