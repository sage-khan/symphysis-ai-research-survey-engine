"""Tests for Agent._resolve_provider(): the seam Phase 2 (plan doc tasks
13-14) added into Agent.run() so a card's runtime_backend selects between
the default direct-completion provider and OpenManusProvider without
touching anything else in the run() pipeline (guardrails, parsing,
retries, storage). Reuses tests/test_qa_precheck.py's _make_agent helper
pattern; no real network or subprocess involved."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest

from symphysis.agent import Agent
from symphysis.agent_card import AgentCardError, ModelSpec, new_card
from symphysis.audit.logger import SurveyStorage
from symphysis.providers import get_provider
from symphysis.runtime.openmanus import OpenManusProvider


def _write_prompt_template(tmp_path: Path) -> Path:
    path = tmp_path / "system_prompt.txt"
    path.write_text("Role: {role}\n{role_description}\n", encoding="utf-8")
    return path


def _make_agent(tmp_path: Path, agent_id: str = "resolve-provider-agent", **card_kwargs) -> Agent:
    survey_dir = tmp_path / "survey"
    card_path = survey_dir / "agents" / f"{agent_id}.json"
    card_path.parent.mkdir(parents=True, exist_ok=True)
    card = new_card(
        agent_id=agent_id,
        role="Data Engineer",
        role_description="A test persona.",
        system_prompt_template=str(_write_prompt_template(tmp_path)),
        model=ModelSpec(provider="ollama", name="test-model"),
        did_seed="test-seed",
        **card_kwargs,
    )
    card.write(card_path)
    storage = SurveyStorage(survey_dir)
    return Agent(card, card_path, storage)


def test_default_card_resolves_to_the_direct_provider(tmp_path):
    agent = _make_agent(tmp_path)  # runtime_backend defaults to "direct_completion"
    provider = agent._resolve_provider()
    assert provider is get_provider("ollama")


def test_openmanus_card_resolves_to_an_openmanus_provider(tmp_path):
    agent = _make_agent(tmp_path, runtime_backend="openmanus")
    provider = agent._resolve_provider()
    assert isinstance(provider, OpenManusProvider)
    assert provider.model_provider == "ollama"
    assert provider.agent_id == "resolve-provider-agent"
    assert provider.did == agent.card.did.id
    # No RAG, no web_search granted for this plain card: only the
    # always-registered, ungated citation_verify tool is present.
    assert set(provider.tools) == {"citation_verify"}
    assert provider.storage is agent.storage


def test_unknown_runtime_backend_raises_agent_card_error(tmp_path):
    agent = _make_agent(tmp_path, runtime_backend="not-a-real-backend")
    with pytest.raises(AgentCardError, match="unknown runtime_backend"):
        agent._resolve_provider()


def test_model_provider_override_beats_the_cards_own_provider(tmp_path, monkeypatch):
    # Phase 4 model-tiering escalation (docs/architecture/governance-layer-and-runtime-backends-plan.md
    # §4): Agent.run()'s escalation check passes model_provider= explicitly
    # when a level triggers escalation to a different provider than the
    # card's own; the card itself is never mutated.
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    agent = _make_agent(tmp_path)  # card.model.provider == "ollama"
    provider = agent._resolve_provider(model_provider="anthropic")
    assert provider is get_provider("anthropic")
    assert agent.card.model.provider == "ollama"  # card itself untouched


def test_model_provider_override_also_applies_on_openmanus_backend(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    agent = _make_agent(tmp_path, runtime_backend="openmanus")
    provider = agent._resolve_provider(model_provider="anthropic")
    assert isinstance(provider, OpenManusProvider)
    assert provider.model_provider == "anthropic"
    assert agent.card.model.provider == "ollama"
