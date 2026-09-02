"""LLM-provider reachability checks, run BEFORE spawning any agent.

Every survey depends on at least one LLM provider actually being reachable
(Ollama running, a hosted-provider API key set). Discovering that it isn't
has historically happened deep into a run, after RAG indexing, QA
prechecks, and however many samples had already started, which wastes real
time and produces a confusing error far from its actual cause. This module
is the single source of truth for "is this provider ready right now,"
checked once, upfront, and reused by both the CLI (`symphysis run`,
verbose output before anything else runs) and the web UI (a status panel
on the survey page, before the Run button is used).

A provider is not required to be reachable to attempt a survey: an agent
whose provider is down is still skipped individually by `orchestrator.py`,
exactly as before. This module's job is only to make that fact known
upfront, not to change what happens when it's ignored.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from .agent_card import load_card
from .config import SurveyConfig

_OLLAMA_PING_TIMEOUT = 5.0

# provider name -> the environment variable its provider class reads (see
# providers/anthropic_provider.py, providers/openai_compatible.py). Kept
# here rather than imported from web/backend/routers/settings.py since
# this module must work standalone (no web/ dependency) for the CLI.
HOSTED_PROVIDER_API_KEY_ENV_VARS = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "groq": "GROQ_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "xai": "XAI_API_KEY",
}


@dataclass
class ProviderStatus:
    provider: str
    ok: bool
    detail: str
    models: Optional[List[str]] = None  # only populated for ollama


def check_ollama(base_url: Optional[str] = None, timeout: float = _OLLAMA_PING_TIMEOUT) -> ProviderStatus:
    url = (base_url or os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")
    try:
        resp = requests.get(f"{url}/api/tags", timeout=timeout)
        resp.raise_for_status()
    except requests.RequestException as exc:
        return ProviderStatus(provider="ollama", ok=False, detail=f"{url} unreachable: {exc}")

    try:
        models = sorted(m["name"] for m in resp.json().get("models", []))
    except (ValueError, KeyError, TypeError):
        return ProviderStatus(provider="ollama", ok=False, detail=f"{url} responded but not with a valid /api/tags body")

    if not models:
        return ProviderStatus(
            provider="ollama", ok=False, detail=f"{url} is reachable but has no models pulled (try `ollama pull <model>`)"
        )
    return ProviderStatus(provider="ollama", ok=True, detail=f"{url} reachable, {len(models)} model(s) available", models=models)


def check_hosted_provider(provider: str) -> ProviderStatus:
    env_var = HOSTED_PROVIDER_API_KEY_ENV_VARS.get(provider)
    if env_var is None:
        return ProviderStatus(provider=provider, ok=False, detail=f"unknown provider '{provider}'")
    if os.environ.get(env_var):
        return ProviderStatus(provider=provider, ok=True, detail=f"{env_var} is set")
    return ProviderStatus(provider=provider, ok=False, detail=f"{env_var} is not set")


def check_claude_cli() -> ProviderStatus:
    # No API key involved (see providers/claude_cli_provider.py): the
    # actual requirement is that the `claude` binary exists and is already
    # logged in via its own subscription auth, which `shutil.which` alone
    # cannot confirm. A cheap, side-effect-free `claude --version` call
    # confirms the binary is real and executable without spending an
    # actual completion call just to run preflight.
    import shutil
    import subprocess

    binary = shutil.which("claude")
    if binary is None:
        return ProviderStatus(provider="claude_cli", ok=False, detail="'claude' binary not found on PATH")
    try:
        result = subprocess.run([binary, "--version"], capture_output=True, text=True, timeout=10)
    except (subprocess.TimeoutExpired, OSError) as exc:
        return ProviderStatus(provider="claude_cli", ok=False, detail=f"'claude --version' failed: {exc}")
    if result.returncode != 0:
        return ProviderStatus(provider="claude_cli", ok=False, detail=f"'claude --version' exited {result.returncode}")
    return ProviderStatus(provider="claude_cli", ok=True, detail=f"{binary} ({result.stdout.strip()})")


def check_manual() -> ProviderStatus:
    # A human pastes every response by hand; there is no automated
    # endpoint to check. Always "ok": the check exists to catch a
    # misconfigured or unreachable *automated* backend, not to comment on
    # a workflow that was never automated in the first place.
    return ProviderStatus(provider="manual", ok=True, detail="human-paste workflow, no endpoint to check")


def check_provider(provider: str) -> ProviderStatus:
    if provider == "ollama":
        return check_ollama()
    if provider == "manual":
        return check_manual()
    if provider == "claude_cli":
        return check_claude_cli()
    return check_hosted_provider(provider)


def check_providers(providers: List[str]) -> List[ProviderStatus]:
    """One check per unique provider name, in the order first seen."""
    seen: List[str] = []
    for p in providers:
        if p not in seen:
            seen.append(p)
    return [check_provider(p) for p in seen]


def check_survey_providers(survey: SurveyConfig) -> List[ProviderStatus]:
    """Every distinct provider actually configured across this survey's
    agent cards. A card that fails to load is skipped here (the same load
    error will surface, clearly, once run_survey() actually attempts it);
    this check only reports on cards that parse."""
    providers: List[str] = []
    for card_path in survey.agent_cards:
        try:
            card = load_card(card_path)
        except Exception:  # noqa: BLE001 - a broken card is reported by run_survey() itself, not here
            continue
        providers.append(card.model.provider)
    return check_providers(providers)


def check_agent_card_paths_providers(card_paths: List[Path]) -> List[ProviderStatus]:
    """Same as check_survey_providers, for callers (the web backend) that
    already have a list of card paths rather than a loaded SurveyConfig."""
    providers: List[str] = []
    for card_path in card_paths:
        try:
            card = load_card(card_path)
        except Exception:  # noqa: BLE001
            continue
        providers.append(card.model.provider)
    return check_providers(providers)


def status_to_dict(status: ProviderStatus) -> Dict[str, Any]:
    return {"provider": status.provider, "ok": status.ok, "detail": status.detail, "models": status.models}
