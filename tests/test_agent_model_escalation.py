"""Tests for Agent.run()'s Phase 4 branch
(docs/architecture/governance-layer-and-runtime-backends-plan.md §4): a
hierarchical instrument run whose survey declares an escalation rule
{"threshold": N, "model": {...}} must switch to that model for any run
where a level exceeds N criteria — unless the card opts out via
escalation_exempt, or the provider is "manual" (no model call to switch),
or the instrument has no levels_for_panel() (escalation is level-count
based and only meaningful for hierarchical instruments). The real provider
construction is stubbed at the same Agent._resolve_provider boundary
tests/test_agent_survey_panel_wiring.py and tests/test_qa_precheck.py use."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from symphysis import agent as agent_module
from symphysis.agent import Agent
from symphysis.agent_card import ModelSpec, new_card
from symphysis.audit.logger import SurveyStorage
from symphysis.instruments.bwm import BWMInstrument
from symphysis.instruments.hierarchical_bwm import HierarchicalBWMInstrument
from symphysis.providers.base import ProviderResponse


class _FakeProvider:
    def __init__(self, response_text: str):
        self.response_text = response_text
        self.calls = []

    def complete(self, messages, *, model, temperature, max_tokens, top_p=1.0, seed=None, **extra):
        self.calls.append({"model": model, "temperature": temperature, "extra": extra})
        return ProviderResponse(text=self.response_text, model=model, finish_reason="stop")


PANEL_PARAMS = {
    "levels": [
        {"id": "L1", "name": "Small level", "description": "d1", "dimensions": ["A", "B"]},
        {"id": "L2", "name": "Big level", "description": "d2", "dimensions": ["A", "B", "C", "D", "E", "F", "G"]},
    ],
}

FLAT_PARAMS = {"dimensions": ["A", "B"]}

ESCALATION = {
    "threshold": 6,
    "model": {"provider": "anthropic", "name": "claude-sonnet-5", "temperature": 0.2, "max_tokens": 4096, "top_p": 0.9},
}

_RUN_RESPONSE = json.dumps({
    "levels": {
        "L1": {"best": "A", "worst": "B", "best_to_others": {"A": 1, "B": 3}, "others_to_worst": {"A": 3, "B": 1}},
        "L2": {
            "best": "A", "worst": "G",
            "best_to_others": {c: 1 for c in "ABCDEFG"},
            "others_to_worst": {c: 1 for c in "ABCDEFG"},
        },
    }
})


def _write_prompt_template(tmp_path: Path) -> Path:
    path = tmp_path / "system_prompt.txt"
    path.write_text("Role: {role}\n{role_description}\n", encoding="utf-8")
    return path


def _make_agent(
    tmp_path: Path, agent_id: str = "escalation-agent", model: ModelSpec = None, **card_kwargs
) -> Agent:
    survey_dir = tmp_path / "survey"
    card_path = survey_dir / "agents" / f"{agent_id}.json"
    card_path.parent.mkdir(parents=True, exist_ok=True)
    card = new_card(
        agent_id=agent_id,
        role="Data Engineer",
        role_description="A test persona.",
        system_prompt_template=str(_write_prompt_template(tmp_path)),
        model=model or ModelSpec(provider="ollama", name="test-model"),
        did_seed="test-seed",
        **card_kwargs,
    )
    card.write(card_path)
    storage = SurveyStorage(survey_dir)
    return Agent(card, card_path, storage)


def _stub_qa_precheck(monkeypatch):
    qa_fake = _FakeProvider('{"role_understood": true, "capabilities_understood": [], "sources_understood": true}')
    monkeypatch.setattr(agent_module, "get_provider", lambda name: qa_fake)


def test_escalation_switches_model_when_a_level_exceeds_threshold(tmp_path, monkeypatch):
    _stub_qa_precheck(monkeypatch)
    agent = _make_agent(tmp_path)
    run_fake = _FakeProvider(_RUN_RESPONSE)
    seen_model_provider = {}

    def _fake_resolve(instrument=None, instrument_params=None, model_provider=None):
        seen_model_provider["value"] = model_provider
        return run_fake

    monkeypatch.setattr(agent, "_resolve_provider", _fake_resolve)

    agent.run(HierarchicalBWMInstrument(), PANEL_PARAMS, escalation=ESCALATION)

    assert seen_model_provider["value"] == "anthropic"
    assert run_fake.calls[0]["model"] == "claude-sonnet-5"
    assert run_fake.calls[0]["temperature"] == 0.2

    conv_path = agent.storage.agent_dir(agent.card.agent_id) / "conversation.jsonl"
    lines = [json.loads(l) for l in conv_path.read_text().splitlines()]
    escalation_events = [l for l in lines if l["kind"] == "model_escalated"]
    assert len(escalation_events) == 1
    assert escalation_events[0]["levels"] == ["L2"]
    assert escalation_events[0]["from_model"] == "ollama/test-model"
    assert escalation_events[0]["to_model"] == "anthropic/claude-sonnet-5"


def test_no_escalation_configured_leaves_the_cards_own_model(tmp_path, monkeypatch):
    _stub_qa_precheck(monkeypatch)
    agent = _make_agent(tmp_path)
    run_fake = _FakeProvider(_RUN_RESPONSE)
    monkeypatch.setattr(agent, "_resolve_provider", lambda *a, **kw: run_fake)

    agent.run(HierarchicalBWMInstrument(), PANEL_PARAMS, escalation={})

    assert run_fake.calls[0]["model"] == "test-model"
    conv_path = agent.storage.agent_dir(agent.card.agent_id) / "conversation.jsonl"
    lines = [json.loads(l) for l in conv_path.read_text().splitlines()]
    assert not [l for l in lines if l["kind"] == "model_escalated"]


def test_no_level_exceeds_threshold_leaves_the_cards_own_model(tmp_path, monkeypatch):
    _stub_qa_precheck(monkeypatch)
    agent = _make_agent(tmp_path)
    run_fake = _FakeProvider(_RUN_RESPONSE)
    monkeypatch.setattr(agent, "_resolve_provider", lambda *a, **kw: run_fake)

    high_threshold_escalation = {**ESCALATION, "threshold": 100}
    agent.run(HierarchicalBWMInstrument(), PANEL_PARAMS, escalation=high_threshold_escalation)

    assert run_fake.calls[0]["model"] == "test-model"


def test_escalation_exempt_card_never_escalates(tmp_path, monkeypatch):
    _stub_qa_precheck(monkeypatch)
    agent = _make_agent(tmp_path, escalation_exempt=True)
    run_fake = _FakeProvider(_RUN_RESPONSE)
    monkeypatch.setattr(agent, "_resolve_provider", lambda *a, **kw: run_fake)

    agent.run(HierarchicalBWMInstrument(), PANEL_PARAMS, escalation=ESCALATION)

    assert run_fake.calls[0]["model"] == "test-model"


def test_manual_provider_never_escalates(tmp_path, monkeypatch):
    # Manual agents skip both the QA precheck and escalation: there is no
    # model call to switch, a human is pasting the response by hand.
    agent = _make_agent(tmp_path, model=ModelSpec(provider="manual", name="human"))
    run_fake = _FakeProvider(_RUN_RESPONSE)
    monkeypatch.setattr(agent, "_resolve_provider", lambda *a, **kw: run_fake)

    agent.run(HierarchicalBWMInstrument(), PANEL_PARAMS, escalation=ESCALATION)

    assert run_fake.calls[0]["model"] == "human"


def test_flat_instrument_never_escalates(tmp_path, monkeypatch):
    # BWMInstrument has no levels_for_panel(): escalation is level-count
    # based and only meaningful for hierarchical instruments, so a flat
    # instrument's run is unaffected even with escalation configured.
    _stub_qa_precheck(monkeypatch)
    agent = _make_agent(tmp_path)
    run_fake = _FakeProvider(json.dumps({
        "best": "A", "worst": "B", "best_to_others": {"A": 1, "B": 3}, "others_to_worst": {"A": 3, "B": 1},
    }))
    monkeypatch.setattr(agent, "_resolve_provider", lambda *a, **kw: run_fake)

    agent.run(BWMInstrument(), FLAT_PARAMS, escalation=ESCALATION)

    assert run_fake.calls[0]["model"] == "test-model"
