import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentic_survey.agent_card import GuardrailsSpec, ModelSpec, PermissionsSpec, RagSpec, SamplingSpec, new_card
from agentic_survey.config import load_survey_config
from agentic_survey.orchestrator import run_survey

DIMENSIONS = ["Q", "PT", "V"]


def _write_prompt_template(config_dir: Path) -> Path:
    path = config_dir / "system_prompt.txt"
    path.write_text("Role: {role}\n{role_description}\n", encoding="utf-8")
    return path


def _write_survey(survey_dir: Path) -> None:
    (survey_dir / "agents").mkdir(parents=True, exist_ok=True)
    survey_yaml = {
        "id": "ahp-test",
        "title": "AHP orchestrator test",
        "instrument": "ahp",
        "instrument_params": {"dimensions": DIMENSIONS, "dimension_labels": {}},
        "weighting": {},
    }
    (survey_dir / "survey.yaml").write_text(yaml.dump(survey_yaml), encoding="utf-8")


def _add_manual_agent(survey_dir: Path, agent_id: str, prompt_template: Path, comparisons: dict) -> None:
    card = new_card(
        agent_id=agent_id,
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
    card.write(survey_dir / "agents" / f"{agent_id}.json")

    manual_dir = survey_dir / "agents" / agent_id / "manual_input"
    manual_dir.mkdir(parents=True)
    (manual_dir / "prompt_00.md").write_text("prompt", encoding="utf-8")
    (manual_dir / "response_00.txt").write_text(
        json.dumps({"comparisons": comparisons, "reasoning": "test", "sources_used": ["general_knowledge"]}),
        encoding="utf-8",
    )


def test_ahp_survey_runs_end_to_end_and_aggregates_two_agents(tmp_path):
    survey_dir = tmp_path / "ahp-test"
    _write_survey(survey_dir)
    prompt_template = _write_prompt_template(tmp_path)

    _add_manual_agent(survey_dir, "agent-one", prompt_template, {"Q_vs_PT": 3, "Q_vs_V": 5, "PT_vs_V": 2})
    _add_manual_agent(survey_dir, "agent-two", prompt_template, {"Q_vs_PT": 2, "Q_vs_V": 4, "PT_vs_V": 2})

    survey = load_survey_config(survey_dir)
    result = run_survey(survey)

    assert result["instrument"] == "ahp"
    assert result["agent_panel"]["num_agents"] == 2
    assert len(result["agent_panel"]["individual_solutions"]) == 2
    weights = result["agent_panel"]["aggregated_weights"]
    assert abs(sum(weights.values()) - 1.0) < 1e-6
    # Both agents rated Q most important in every comparison, so it should
    # dominate the aggregated weights too.
    assert weights["Q"] > weights["PT"] > weights["V"]

    report_path = survey_dir / "report" / "report.md"
    assert report_path.exists()
    report_text = report_path.read_text(encoding="utf-8")
    assert "Analytic Hierarchy Process" in report_text
    assert "## Methodology" in report_text
    assert "## Per-agent detail" in report_text
    assert "agent-one" in report_text and "agent-two" in report_text
    assert "test" in report_text  # the manual agents' shared "reasoning": "test"
    assert "not applicable (manual-provider agent)" in report_text  # manual agents skip QA precheck
    assert "![Ahp Aggregated Weights](charts/ahp_aggregated_weights.png)" in report_text

    manifest_path = survey_dir / "integrity_manifest.json"
    assert manifest_path.exists()
