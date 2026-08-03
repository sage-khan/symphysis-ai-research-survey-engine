"""Tests for the QA precheck (Agent.run_qa_precheck), the global/agent
rulefile injection, and the per-sample sources_used verification wired
through storage.write_guarded_run. Providers are faked at the
agent_module.get_provider boundary, never the real network."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentic_survey import agent as agent_module
from agentic_survey import app_config
from agentic_survey.agent import Agent
from agentic_survey.agent_card import ModelSpec, new_card
from agentic_survey.guardrails import GuardedRun
from agentic_survey.instruments.base import InstrumentResult
from agentic_survey.providers.base import ProviderResponse
from agentic_survey.storage import SurveyStorage


class _FakeProvider:
    def __init__(self, response_text: str):
        self.response_text = response_text
        self.calls = []

    def complete(self, messages, *, model, temperature, max_tokens, top_p=1.0, seed=None, **extra):
        self.calls.append(messages)
        return ProviderResponse(text=self.response_text, model=model, finish_reason="stop")


def _write_prompt_template(tmp_path: Path) -> Path:
    path = tmp_path / "system_prompt.txt"
    path.write_text("Role: {role}\n{role_description}\n", encoding="utf-8")
    return path


def _make_agent(tmp_path: Path, agent_id: str = "qa-test-agent", **card_kwargs) -> Agent:
    survey_dir = tmp_path / "survey"
    survey_dir.mkdir(parents=True, exist_ok=True)
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


def test_role_description_appends_global_and_agent_rulefiles(tmp_path, monkeypatch):
    monkeypatch.setattr(app_config, "GLOBAL_RULEFILE_PATH", tmp_path / "global_rulefile.md")
    app_config.save_global_rulefile("Never fabricate a source.")
    agent = _make_agent(tmp_path, rulefile="Weigh legal sensitivity heavily.")
    description = agent._role_description()
    assert "Never fabricate a source." in description
    assert "Weigh legal sensitivity heavily." in description
    assert "Rules you must follow" in description
    assert "Additional rules for this agent" in description


def test_role_description_omits_rules_section_when_both_are_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(app_config, "GLOBAL_RULEFILE_PATH", tmp_path / "does-not-exist.md")
    agent = _make_agent(tmp_path)
    description = agent._role_description()
    assert "Rules you must follow" not in description


def test_qa_precheck_ground_truth_reflects_real_configuration(tmp_path, monkeypatch):
    monkeypatch.setattr(app_config, "GLOBAL_RULEFILE_PATH", tmp_path / "does-not-exist.md")
    agent = _make_agent(tmp_path, role_pack="data_engineer", tools=["web_search"])
    truth = agent._qa_precheck_ground_truth()
    assert truth["agent_id"] == "qa-test-agent"
    assert truth["role"] == "Data Engineer"
    assert truth["model"] == "ollama/test-model"
    assert truth["capabilities"]["role_pack"] == "data_engineer"
    assert truth["capabilities"]["web_search"] is True
    assert truth["capabilities"]["dedicated_rag_corpus"] is False
    assert truth["capabilities"]["shared_knowledge_repo"] is False


def test_run_qa_precheck_passes_when_agent_restates_configuration_exactly(tmp_path, monkeypatch):
    monkeypatch.setattr(app_config, "GLOBAL_RULEFILE_PATH", tmp_path / "does-not-exist.md")
    agent = _make_agent(tmp_path)
    truth = agent._qa_precheck_ground_truth()
    honest_response = json.dumps(
        {
            "agent_id": truth["agent_id"],
            "role": truth["role"],
            "model": truth["model"],
            "capabilities": truth["capabilities"],
            "acknowledgement": "Understood, I will attempt this as an expert data engineer.",
        }
    )
    fake_provider = _FakeProvider(honest_response)
    monkeypatch.setattr(agent_module, "get_provider", lambda name: fake_provider)

    agent.run_qa_precheck("Test survey")

    qa_path = agent.storage.agent_dir(agent.card.agent_id) / "qa_precheck.json"
    assert qa_path.exists()
    logged = json.loads(qa_path.read_text(encoding="utf-8"))
    assert logged["verification"]["all_match"] is True


def test_run_qa_precheck_flags_a_hallucinated_capability(tmp_path, monkeypatch):
    monkeypatch.setattr(app_config, "GLOBAL_RULEFILE_PATH", tmp_path / "does-not-exist.md")
    agent = _make_agent(tmp_path)  # no web_search granted
    truth = agent._qa_precheck_ground_truth()
    dishonest_response = json.dumps(
        {
            "agent_id": truth["agent_id"],
            "role": truth["role"],
            "model": truth["model"],
            "capabilities": {**truth["capabilities"], "web_search": True},  # hallucinated
            "acknowledgement": "Understood.",
        }
    )
    fake_provider = _FakeProvider(dishonest_response)
    monkeypatch.setattr(agent_module, "get_provider", lambda name: fake_provider)

    agent.run_qa_precheck("Test survey")

    logged = json.loads((agent.storage.agent_dir(agent.card.agent_id) / "qa_precheck.json").read_text(encoding="utf-8"))
    assert logged["verification"]["all_match"] is False
    assert logged["verification"]["field_matches"]["web_search"] is False


def test_run_qa_precheck_handles_unparseable_response_without_raising(tmp_path, monkeypatch):
    monkeypatch.setattr(app_config, "GLOBAL_RULEFILE_PATH", tmp_path / "does-not-exist.md")
    agent = _make_agent(tmp_path)
    fake_provider = _FakeProvider("I'm not going to answer in JSON, sorry.")
    monkeypatch.setattr(agent_module, "get_provider", lambda name: fake_provider)

    agent.run_qa_precheck("Test survey")  # must not raise

    logged = json.loads((agent.storage.agent_dir(agent.card.agent_id) / "qa_precheck.json").read_text(encoding="utf-8"))
    assert logged["claimed"] is None
    assert logged["verification"]["all_match"] is False


def _guarded_run_with_payload(payload: dict) -> GuardedRun:
    result = InstrumentResult(valid=True, payload=payload, errors=[])
    raw = ProviderResponse(text=json.dumps(payload), model="test-model", finish_reason="stop")
    return GuardedRun(accepted=[result], rejected=[], raw_completions=[raw], accepted_raw=[raw], flagged_low_agreement=False)


def test_write_guarded_run_flags_a_fabricated_source_citation(tmp_path, monkeypatch):
    monkeypatch.setattr(app_config, "GLOBAL_RULEFILE_PATH", tmp_path / "does-not-exist.md")
    agent = _make_agent(tmp_path)
    payload = {
        "best": "Q",
        "worst": "C",
        "best_to_others": {"Q": 1, "C": 8},
        "others_to_worst": {"Q": 8, "C": 1},
        "reasoning": "Quality matters most.",
        "sources_used": ["web: some source"],  # never actually available
    }
    run = _guarded_run_with_payload(payload)
    agent.storage.write_guarded_run(agent.card.agent_id, run, context_chunks=[])

    result = json.loads((agent.storage.agent_dir(agent.card.agent_id) / "result.json").read_text(encoding="utf-8"))
    assert result["sources_checks"][0]["genuine"] is False
    assert "web: some source" in result["sources_checks"][0]["fabricated"]

    conversation = (agent.storage.agent_dir(agent.card.agent_id) / "conversation.jsonl").read_text(encoding="utf-8")
    assert "fabricated_source_citation" in conversation


def test_write_guarded_run_accepts_a_genuine_source_citation(tmp_path, monkeypatch):
    monkeypatch.setattr(app_config, "GLOBAL_RULEFILE_PATH", tmp_path / "does-not-exist.md")
    agent = _make_agent(tmp_path)
    payload = {
        "best": "Q",
        "worst": "C",
        "best_to_others": {"Q": 1, "C": 8},
        "others_to_worst": {"Q": 8, "C": 1},
        "reasoning": "Quality matters most.",
        "sources_used": ["general_knowledge"],
    }
    run = _guarded_run_with_payload(payload)
    agent.storage.write_guarded_run(agent.card.agent_id, run, context_chunks=[])

    result = json.loads((agent.storage.agent_dir(agent.card.agent_id) / "result.json").read_text(encoding="utf-8"))
    assert result["sources_checks"][0]["genuine"] is True

    conversation = (agent.storage.agent_dir(agent.card.agent_id) / "conversation.jsonl").read_text(encoding="utf-8")
    assert "fabricated_source_citation" not in conversation
