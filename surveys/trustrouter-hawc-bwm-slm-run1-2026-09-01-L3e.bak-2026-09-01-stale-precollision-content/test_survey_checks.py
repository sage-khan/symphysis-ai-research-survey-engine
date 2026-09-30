import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from symphysis.agent_card import GuardrailsSpec, ModelSpec, PermissionsSpec, RagSpec, SamplingSpec, new_card
from symphysis.survey_checks import fix_survey

DIMENSIONS = ["Q", "PT", "V", "IC", "L", "C"]


def _write_survey(survey_dir: Path, instrument_params=None) -> None:
    (survey_dir / "agents").mkdir(parents=True, exist_ok=True)
    survey_yaml = {
        "id": "checks-test",
        "title": "Checks test",
        "instrument": "bwm",
        "instrument_params": instrument_params or {"dimensions": DIMENSIONS, "dimension_labels": {}},
        "weighting": {},
    }
    (survey_dir / "survey.yaml").write_text(yaml.dump(survey_yaml), encoding="utf-8")


def _write_card(survey_dir: Path, prompt_template: Path, **kwargs) -> None:
    card = new_card(
        agent_id="test-agent",
        role="Reviewer",
        role_description="A reviewer.",
        system_prompt_template=str(prompt_template),
        model=ModelSpec(provider="manual", name="gemini-2.5-pro"),
        rag=kwargs.pop("rag", RagSpec(enabled=False)),
        sampling=SamplingSpec(repeats=1, max_retries_on_malformed=0),
        permissions=PermissionsSpec(allowed_providers=["manual"]),
        guardrails=GuardrailsSpec(),
        did_seed="checks-test-seed",
        **kwargs,
    )
    card.write(survey_dir / "agents" / "test-agent.json")


def test_fix_survey_reports_no_problems_for_a_clean_survey(tmp_path):
    survey_dir = tmp_path / "clean-survey"
    _write_survey(survey_dir)
    prompt_template = tmp_path / "system_prompt.txt"
    prompt_template.write_text("Role: {role}\n{role_description}\n", encoding="utf-8")
    _write_card(survey_dir, prompt_template)

    assert fix_survey(survey_dir) == []


def test_fix_survey_reports_missing_survey_yaml(tmp_path):
    survey_dir = tmp_path / "missing-survey"
    survey_dir.mkdir()
    problems = fix_survey(survey_dir)
    assert len(problems) == 1
    assert "survey.yaml" in problems[0]


def test_fix_survey_reports_a_dangling_rag_corpus_path(tmp_path):
    survey_dir = tmp_path / "dangling-rag"
    _write_survey(survey_dir)
    prompt_template = tmp_path / "system_prompt.txt"
    prompt_template.write_text("Role: {role}\n{role_description}\n", encoding="utf-8")
    _write_card(survey_dir, prompt_template, rag=RagSpec(enabled=True, corpus_path=str(tmp_path / "no-such-dir")))

    problems = fix_survey(survey_dir)
    assert any("does not exist as a directory" in p for p in problems)


def test_fix_survey_reports_an_unknown_role_pack(tmp_path):
    survey_dir = tmp_path / "bad-role-pack"
    _write_survey(survey_dir)
    prompt_template = tmp_path / "system_prompt.txt"
    prompt_template.write_text("Role: {role}\n{role_description}\n", encoding="utf-8")
    _write_card(survey_dir, prompt_template, role_pack="not_a_real_pack")

    problems = fix_survey(survey_dir)
    assert any("does not match any known role pack" in p for p in problems)


def test_fix_survey_reports_a_missing_system_prompt_template(tmp_path):
    survey_dir = tmp_path / "missing-template"
    _write_survey(survey_dir)
    _write_card(survey_dir, tmp_path / "no-such-template.txt")

    problems = fix_survey(survey_dir)
    assert any("system_prompt_template" in p for p in problems)


def test_fix_survey_reports_hierarchical_bwm_with_no_root_level(tmp_path):
    survey_dir = tmp_path / "no-root"
    (survey_dir / "agents").mkdir(parents=True)
    (survey_dir / "survey.yaml").write_text(
        yaml.dump({
            "id": "checks-test", "title": "Checks test", "instrument": "hierarchical_bwm",
            "instrument_params": {
                "levels": [
                    {"id": "L1", "dimensions": ["A", "B"], "parent_level": "L0", "parent_criterion": "A"},
                ]
            },
            "weighting": {},
        }),
        encoding="utf-8",
    )
    prompt_template = tmp_path / "system_prompt.txt"
    prompt_template.write_text("Role: {role}\n{role_description}\n", encoding="utf-8")
    _write_card(survey_dir, prompt_template, instrument="hierarchical_bwm")

    problems = fix_survey(survey_dir)
    assert any("no root level" in p for p in problems)
    assert any("not a known level id" in p for p in problems)
