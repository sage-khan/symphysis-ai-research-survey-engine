"""Tests for Agent.run()'s Phase 3 branch: a hierarchical instrument run
through an openmanus-backend card must build extra_call_kwargs shaped for
runtime/openmanus.py's "survey_panel" flow (flow/levels/level_messages),
instead of the plain single-shot call every other backend/instrument
combination still uses. The real provider construction and the isolated
OpenManus subprocess are both stubbed out here (see
tests/test_runtime_openmanus.py and tests/test_tools_proxy.py for the
real-subprocess-level tests) — this file only verifies run()'s own wiring
decision, at the agent_module.get_provider / Agent._resolve_provider
boundary, matching tests/test_qa_precheck.py's established pattern."""

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
        self.calls.append({"messages": messages, "extra": extra})
        return ProviderResponse(text=self.response_text, model=model, finish_reason="stop")


PANEL_PARAMS = {
    "levels": [
        {"id": "L1", "name": "Top-level factors", "description": "d1", "dimensions": ["DVS", "F"]},
    ],
}

FLAT_PARAMS = {"dimensions": ["DVS", "F"]}


def _write_prompt_template(tmp_path: Path) -> Path:
    path = tmp_path / "system_prompt.txt"
    path.write_text("Role: {role}\n{role_description}\n", encoding="utf-8")
    return path


def _make_agent(tmp_path: Path, agent_id: str = "panel-wiring-agent", **card_kwargs) -> Agent:
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


def _stub_qa_precheck(monkeypatch):
    qa_fake = _FakeProvider('{"role_understood": true, "capabilities_understood": [], "sources_understood": true}')
    monkeypatch.setattr(agent_module, "get_provider", lambda name: qa_fake)


def test_hierarchical_instrument_on_openmanus_backend_gets_survey_panel_extra_kwargs(tmp_path, monkeypatch):
    _stub_qa_precheck(monkeypatch)
    agent = _make_agent(tmp_path, runtime_backend="openmanus")
    run_fake = _FakeProvider(json.dumps({
        "levels": {
            "L1": {
                "best": "DVS", "worst": "F",
                "best_to_others": {"DVS": 1, "F": 3},
                "others_to_worst": {"DVS": 3, "F": 1},
            }
        }
    }))
    monkeypatch.setattr(agent, "_resolve_provider", lambda instrument=None, instrument_params=None: run_fake)

    agent.run(HierarchicalBWMInstrument(), PANEL_PARAMS)

    # SamplingSpec.repeats defaults to more than one independent sample per
    # agent; every one of them must carry the same panel-flow extra kwargs.
    assert len(run_fake.calls) >= 1
    extra = run_fake.calls[0]["extra"]
    assert extra["flow"] == "survey_panel"
    assert extra["levels"] == PANEL_PARAMS["levels"]
    assert set(extra["level_messages"]) == {"L1"}
    level_content = extra["level_messages"]["L1"][1]["content"]
    assert 'level_id="L1"' in level_content


def test_hierarchical_instrument_on_direct_completion_backend_gets_no_panel_kwargs(tmp_path, monkeypatch):
    _stub_qa_precheck(monkeypatch)
    agent = _make_agent(tmp_path)  # runtime_backend defaults to "direct_completion"
    run_fake = _FakeProvider(json.dumps({
        "levels": {
            "L1": {
                "best": "DVS", "worst": "F",
                "best_to_others": {"DVS": 1, "F": 3},
                "others_to_worst": {"DVS": 3, "F": 1},
            }
        }
    }))
    monkeypatch.setattr(agent, "_resolve_provider", lambda instrument=None, instrument_params=None: run_fake)

    agent.run(HierarchicalBWMInstrument(), PANEL_PARAMS)

    assert len(run_fake.calls) >= 1
    assert "flow" not in run_fake.calls[0]["extra"]


def test_flat_instrument_on_openmanus_backend_gets_no_panel_kwargs(tmp_path, monkeypatch):
    # BWMInstrument has no levels_for_panel(): hasattr(...) gates the panel
    # branch off entirely, even though runtime_backend is "openmanus".
    _stub_qa_precheck(monkeypatch)
    agent = _make_agent(tmp_path, runtime_backend="openmanus")
    run_fake = _FakeProvider(json.dumps({
        "best": "DVS", "worst": "F",
        "best_to_others": {"DVS": 1, "F": 3},
        "others_to_worst": {"DVS": 3, "F": 1},
    }))
    monkeypatch.setattr(agent, "_resolve_provider", lambda instrument=None, instrument_params=None: run_fake)

    agent.run(BWMInstrument(), FLAT_PARAMS)

    assert len(run_fake.calls) >= 1
    assert "flow" not in run_fake.calls[0]["extra"]
