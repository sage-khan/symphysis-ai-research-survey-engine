"""Tests for SurveyConfig's Phase 4 escalation field
(docs/architecture/governance-layer-and-runtime-backends-plan.md §4): {}
(the default, and every survey.yaml written before this field existed)
means "no escalation configured" and must round-trip correctly through
load_survey_config()."""

import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from symphysis.agent_card import ModelSpec, new_card
from symphysis.config import load_survey_config


def _write_agent_card(survey_dir: Path) -> None:
    (survey_dir / "agents").mkdir(parents=True, exist_ok=True)
    card = new_card(
        agent_id="only-agent",
        role="Reviewer",
        role_description="A reviewer.",
        system_prompt_template="config/prompts/expert_panel_system.txt",
        model=ModelSpec(provider="ollama", name="qwen2.5:14b"),
        did_seed="test-seed",
    )
    card.write(survey_dir / "agents" / "only-agent.json")


def test_survey_yaml_without_escalation_field_defaults_to_empty_dict(tmp_path):
    survey_dir = tmp_path / "survey"
    survey_dir.mkdir()
    _write_agent_card(survey_dir)
    (survey_dir / "survey.yaml").write_text(
        yaml.dump({"id": "s1", "title": "Survey 1", "instrument": "bwm"}), encoding="utf-8"
    )

    survey = load_survey_config(survey_dir)
    assert survey.escalation == {}


def test_survey_yaml_with_explicit_null_escalation_defaults_to_empty_dict(tmp_path):
    # A hand-edited survey.yaml with "escalation:" and nothing after it
    # parses to None via yaml.safe_load, not {} — load_survey_config must
    # still normalize that to {}, not leak a bare None into SurveyConfig.
    survey_dir = tmp_path / "survey"
    survey_dir.mkdir()
    _write_agent_card(survey_dir)
    (survey_dir / "survey.yaml").write_text(
        yaml.dump({"id": "s1", "title": "Survey 1", "instrument": "bwm", "escalation": None}), encoding="utf-8"
    )

    survey = load_survey_config(survey_dir)
    assert survey.escalation == {}


def test_survey_yaml_with_escalation_loads_the_full_shape(tmp_path):
    survey_dir = tmp_path / "survey"
    survey_dir.mkdir()
    _write_agent_card(survey_dir)
    escalation = {
        "threshold": 6,
        "model": {"provider": "anthropic", "name": "claude-sonnet-5", "temperature": 0.7, "max_tokens": 2048, "top_p": 1.0},
    }
    (survey_dir / "survey.yaml").write_text(
        yaml.dump({"id": "s1", "title": "Survey 1", "instrument": "hierarchical_bwm", "escalation": escalation}),
        encoding="utf-8",
    )

    survey = load_survey_config(survey_dir)
    assert survey.escalation == escalation
