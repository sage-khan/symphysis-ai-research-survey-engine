import json
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentic_survey.agent_card import GuardrailsSpec, ModelSpec, PermissionsSpec, RagSpec, SamplingSpec, new_card
from agentic_survey.config import load_survey_config
from agentic_survey.orchestrator import regenerate_report, run_survey

DIMENSIONS = ["Q", "PT", "V", "IC", "L", "C"]


def _write_survey(survey_dir: Path) -> None:
    (survey_dir / "agents").mkdir(parents=True, exist_ok=True)
    survey_yaml = {
        "id": "regen-test",
        "title": "Regen test",
        "instrument": "bwm",
        "instrument_params": {"dimensions": DIMENSIONS, "dimension_labels": {}},
        "weighting": {},
    }
    (survey_dir / "survey.yaml").write_text(yaml.dump(survey_yaml), encoding="utf-8")


def _write_manual_card(survey_dir: Path, prompt_template: Path) -> None:
    card = new_card(
        agent_id="manual-agent",
        role="Reviewer",
        role_description="A reviewer.",
        system_prompt_template=str(prompt_template),
        model=ModelSpec(provider="manual", name="gemini-2.5-pro"),
        rag=RagSpec(enabled=False),
        sampling=SamplingSpec(repeats=1, max_retries_on_malformed=0),
        permissions=PermissionsSpec(allowed_providers=["manual"]),
        guardrails=GuardrailsSpec(),
        did_seed="regen-test-seed",
    )
    card.write(survey_dir / "agents" / "manual-agent.json")

    manual_dir = survey_dir / "agents" / "manual-agent" / "manual_input"
    manual_dir.mkdir(parents=True)
    (manual_dir / "prompt_00.md").write_text("prompt", encoding="utf-8")
    (manual_dir / "response_00.txt").write_text(
        json.dumps({
            "best": "PT", "worst": "C",
            "best_to_others": {"Q": 2, "PT": 1, "V": 3, "IC": 4, "L": 2, "C": 8},
            "others_to_worst": {"Q": 4, "PT": 8, "V": 5, "IC": 3, "L": 4, "C": 1},
            "reasoning": "original",
        }),
        encoding="utf-8",
    )


def test_regenerate_report_replays_accepted_samples_from_disk(tmp_path):
    survey_dir = tmp_path / "regen-test"
    _write_survey(survey_dir)
    prompt_template = tmp_path / "system_prompt.txt"
    prompt_template.write_text("Role: {role}\n{role_description}\n", encoding="utf-8")
    _write_manual_card(survey_dir, prompt_template)

    survey = load_survey_config(survey_dir)
    run_survey(survey)

    sample_path = survey_dir / "agents" / "manual-agent" / "samples" / "sample_00.json"
    assert sample_path.exists()

    regenerated = regenerate_report(survey)
    assert regenerated["agent_panel"]["num_agents"] == 1


def test_regenerate_report_picks_up_a_hand_edited_sample(tmp_path):
    survey_dir = tmp_path / "regen-edit-test"
    _write_survey(survey_dir)
    prompt_template = tmp_path / "system_prompt.txt"
    prompt_template.write_text("Role: {role}\n{role_description}\n", encoding="utf-8")
    _write_manual_card(survey_dir, prompt_template)

    survey = load_survey_config(survey_dir)
    run_survey(survey)

    sample_path = survey_dir / "agents" / "manual-agent" / "samples" / "sample_00.json"
    payload = json.loads(sample_path.read_text(encoding="utf-8"))
    assert payload["reasoning"] == "original"
    payload["reasoning"] = "hand-corrected after review"
    sample_path.write_text(json.dumps(payload), encoding="utf-8")

    # No new manual_input/response file is queued: regenerate_report must
    # never call a provider, only replay what's already on disk.
    regenerated = regenerate_report(survey)
    assert regenerated["agent_panel"]["num_agents"] == 1
    report_md = (survey_dir / "report" / "report.md").read_text(encoding="utf-8")
    assert "hand-corrected after review" in report_md


def test_regenerate_report_raises_clearly_with_no_samples_on_disk(tmp_path):
    survey_dir = tmp_path / "regen-empty-test"
    _write_survey(survey_dir)
    prompt_template = tmp_path / "system_prompt.txt"
    prompt_template.write_text("Role: {role}\n{role_description}\n", encoding="utf-8")
    card = new_card(
        agent_id="never-run-agent",
        role="Reviewer",
        role_description="A reviewer.",
        system_prompt_template=str(prompt_template),
        model=ModelSpec(provider="manual", name="gemini-2.5-pro"),
        rag=RagSpec(enabled=False),
        sampling=SamplingSpec(repeats=1, max_retries_on_malformed=0),
        permissions=PermissionsSpec(allowed_providers=["manual"]),
        guardrails=GuardrailsSpec(),
        did_seed="regen-empty-seed",
    )
    card.write(survey_dir / "agents" / "never-run-agent.json")

    survey = load_survey_config(survey_dir)
    with pytest.raises(RuntimeError, match="nothing to solve"):
        regenerate_report(survey)
