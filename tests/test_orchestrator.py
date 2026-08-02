import json
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentic_survey.agent_card import GuardrailsSpec, ModelSpec, PermissionsSpec, RagSpec, SamplingSpec, new_card
from agentic_survey.config import load_survey_config
from agentic_survey.orchestrator import run_survey

DIMENSIONS = ["Q", "PT", "V", "IC", "L", "C"]


def _write_prompt_template(config_dir: Path) -> Path:
    path = config_dir / "system_prompt.txt"
    path.write_text("Role: {role}\n{role_description}\n", encoding="utf-8")
    return path


def _write_survey(survey_dir: Path) -> None:
    (survey_dir / "agents").mkdir(parents=True, exist_ok=True)
    survey_yaml = {
        "id": "resilience-test",
        "title": "Resilience test",
        "instrument": "bwm",
        "instrument_params": {"dimensions": DIMENSIONS, "dimension_labels": {}},
        "weighting": {},
    }
    (survey_dir / "survey.yaml").write_text(yaml.dump(survey_yaml), encoding="utf-8")


def test_survey_completes_using_manual_agent_when_anthropic_agent_has_no_api_key(tmp_path, monkeypatch):
    """A card configured for provider: anthropic with no ANTHROPIC_API_KEY set
    must be skipped (logged, not a crash), while a manual agent with an
    already-pasted response still lets the survey produce a result."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    survey_dir = tmp_path / "resilience-test"
    _write_survey(survey_dir)
    prompt_template = _write_prompt_template(tmp_path)

    broken_card = new_card(
        agent_id="broken-anthropic-agent",
        role="Reviewer",
        role_description="A reviewer.",
        system_prompt_template=str(prompt_template),
        model=ModelSpec(provider="anthropic", name="claude-opus-5"),
        rag=RagSpec(enabled=False),
        sampling=SamplingSpec(repeats=1, max_retries_on_malformed=0),
        permissions=PermissionsSpec(allowed_providers=["anthropic"]),
        guardrails=GuardrailsSpec(),
        did_seed="test-seed",
    )
    broken_card.write(survey_dir / "agents" / "broken-anthropic-agent.json")

    working_card = new_card(
        agent_id="working-manual-agent",
        role="Reviewer",
        role_description="A reviewer.",
        system_prompt_template=str(prompt_template),
        model=ModelSpec(provider="manual", name="gemini-2.5-pro"),
        rag=RagSpec(enabled=False),
        sampling=SamplingSpec(repeats=1, max_retries_on_malformed=0),
        permissions=PermissionsSpec(allowed_providers=["manual"]),
        guardrails=GuardrailsSpec(),
        did_seed="test-seed",
    )
    card_path = survey_dir / "agents" / "working-manual-agent.json"
    working_card.write(card_path)

    # Pre-seed the manual response so this agent succeeds without a live pass.
    manual_dir = survey_dir / "agents" / "working-manual-agent" / "manual_input"
    manual_dir.mkdir(parents=True)
    (manual_dir / "prompt_00.md").write_text("prompt", encoding="utf-8")
    (manual_dir / "response_00.txt").write_text(
        json.dumps(
            {
                "best": "PT",
                "worst": "C",
                "best_to_others": {"Q": 2, "PT": 1, "V": 3, "IC": 4, "L": 2, "C": 8},
                "others_to_worst": {"Q": 4, "PT": 8, "V": 5, "IC": 3, "L": 4, "C": 1},
                "reasoning": "test",
            }
        ),
        encoding="utf-8",
    )

    survey = load_survey_config(survey_dir)
    result = run_survey(survey)

    assert result["agent_panel"]["num_agents"] == 1
    agent_ids = [m["agent_id"] for m in result["agent_panel"]["per_agent_meta"]]
    assert agent_ids == ["working-manual-agent"]


def test_survey_raises_clearly_when_every_agent_is_skipped(tmp_path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    survey_dir = tmp_path / "all-broken"
    _write_survey(survey_dir)
    prompt_template = _write_prompt_template(tmp_path)

    broken_card = new_card(
        agent_id="broken-anthropic-agent",
        role="Reviewer",
        role_description="A reviewer.",
        system_prompt_template=str(prompt_template),
        model=ModelSpec(provider="anthropic", name="claude-opus-5"),
        rag=RagSpec(enabled=False),
        sampling=SamplingSpec(repeats=1, max_retries_on_malformed=0),
        permissions=PermissionsSpec(allowed_providers=["anthropic"]),
        guardrails=GuardrailsSpec(),
        did_seed="test-seed",
    )
    broken_card.write(survey_dir / "agents" / "broken-anthropic-agent.json")

    survey = load_survey_config(survey_dir)
    with pytest.raises(RuntimeError, match="Some agents were skipped"):
        run_survey(survey)
