"""Tests for SurveyConfig's `pipeline` field (spawning/pipeline.py): {} (the
default, and every survey.yaml written before this field existed) means no
pipeline stage runs, and must round-trip correctly through
load_survey_config(), the same pattern already used for `escalation`
(see test_config_escalation.py)."""

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


def test_survey_yaml_without_pipeline_field_defaults_to_empty_dict(tmp_path):
    survey_dir = tmp_path / "survey"
    survey_dir.mkdir()
    _write_agent_card(survey_dir)
    (survey_dir / "survey.yaml").write_text(
        yaml.dump({"id": "s1", "title": "Survey 1", "instrument": "bwm"}), encoding="utf-8"
    )

    survey = load_survey_config(survey_dir)
    assert survey.pipeline == {}


def test_survey_yaml_with_explicit_null_pipeline_defaults_to_empty_dict(tmp_path):
    survey_dir = tmp_path / "survey"
    survey_dir.mkdir()
    _write_agent_card(survey_dir)
    (survey_dir / "survey.yaml").write_text(
        "id: s1\ntitle: Survey 1\ninstrument: bwm\npipeline:\n", encoding="utf-8"
    )

    survey = load_survey_config(survey_dir)
    assert survey.pipeline == {}


def test_survey_yaml_with_pipeline_stages_round_trips(tmp_path):
    survey_dir = tmp_path / "survey"
    survey_dir.mkdir()
    _write_agent_card(survey_dir)
    (survey_dir / "survey.yaml").write_text(
        yaml.dump(
            {
                "id": "s1",
                "title": "Survey 1",
                "instrument": "bwm",
                "pipeline": {
                    "setup_review": {"agent_card": "pipeline_agents/setup-fixer.json"},
                    "response_review": {"agent_card": "pipeline_agents/response-reviewer.json"},
                },
            }
        ),
        encoding="utf-8",
    )

    survey = load_survey_config(survey_dir)
    assert survey.pipeline["setup_review"]["agent_card"] == "pipeline_agents/setup-fixer.json"
    assert survey.pipeline["response_review"]["agent_card"] == "pipeline_agents/response-reviewer.json"
