"""Tests for the survey-level rulefile tier: between the global rulefile
and an agent's own rulefile, applied to every agent in one specific
survey."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentic_survey import app_config
from agentic_survey.agent import Agent
from agentic_survey.agent_card import ModelSpec, new_card
from agentic_survey.storage import SurveyStorage


def _write_prompt_template(tmp_path: Path) -> Path:
    path = tmp_path / "system_prompt.txt"
    path.write_text("Role: {role}\n{role_description}\n", encoding="utf-8")
    return path


def _make_agent(tmp_path: Path, **card_kwargs) -> Agent:
    survey_dir = tmp_path / "survey"
    survey_dir.mkdir(parents=True, exist_ok=True)
    card_path = survey_dir / "agents" / "agent.json"
    card_path.parent.mkdir(parents=True, exist_ok=True)
    card = new_card(
        agent_id="agent",
        role="Tester",
        role_description="A test persona.",
        system_prompt_template=str(_write_prompt_template(tmp_path)),
        model=ModelSpec(provider="ollama", name="test-model"),
        did_seed="test-seed",
        **card_kwargs,
    )
    card.write(card_path)
    storage = SurveyStorage(survey_dir)
    return Agent(card, card_path, storage)


def test_survey_rulefile_is_included_between_global_and_agent_rules(tmp_path, monkeypatch):
    monkeypatch.setattr(app_config, "GLOBAL_RULEFILE_PATH", tmp_path / "does-not-exist.md")
    agent = _make_agent(tmp_path, rulefile="Agent-specific rule.")
    (agent.storage.root / "rulefile.md").write_text("Survey-specific rule about TrustRouter dimensions.", encoding="utf-8")

    description = agent._role_description()
    assert "Rules for this survey" in description
    assert "Survey-specific rule about TrustRouter dimensions." in description
    assert "Agent-specific rule." in description
    # Ordering: survey rules appear before the agent-specific section
    assert description.index("Rules for this survey") < description.index("Additional rules for this agent")


def test_no_survey_rulefile_section_when_no_rulefile_md_exists(tmp_path, monkeypatch):
    monkeypatch.setattr(app_config, "GLOBAL_RULEFILE_PATH", tmp_path / "does-not-exist.md")
    agent = _make_agent(tmp_path)
    description = agent._role_description()
    assert "Rules for this survey" not in description
