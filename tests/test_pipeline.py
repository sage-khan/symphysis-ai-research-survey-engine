"""Tests for spawning/pipeline.py: setup_review and response_review stages
really exercise spawn.py's mint_child/declare_child attenuation (a genuine
child spawn, not a special-cased path) — same fake-provider boundary used
throughout this suite (tests/test_agent_model_escalation.py,
tests/test_qa_precheck.py): Agent._resolve_provider's direct_completion
branch ultimately calls providers.get_provider, monkeypatched here at the
`symphysis.agent` module's own reference to it, exactly as those tests do."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from symphysis import agent as agent_module
from symphysis.agent_card import ModelSpec, new_card
from symphysis.audit.logger import SurveyStorage
from symphysis.config import SurveyConfig
from symphysis.providers.base import ProviderResponse
from symphysis.spawning import lineage, pipeline

_QA_RESPONSE = json.dumps(
    {
        "agent_id": "x",
        "role": "x",
        "model": "ollama/test-model",
        "capabilities": {"dedicated_rag_corpus": False, "shared_knowledge_repo": False, "role_pack": None, "web_search": False},
        "acknowledgement": "Understood.",
    }
)

_SETUP_REVIEW_RESPONSE = json.dumps(
    {
        "findings": [
            {
                "severity": "warning",
                "area": "dimensions",
                "finding": "Dimension X is ambiguous.",
                "proposed_fix": "Clarify X's definition.",
            }
        ],
        "summary": "Mostly ready; one wording issue.",
    }
)

_RESPONSE_REVIEW_RESPONSE = json.dumps(
    {
        "findings": [{"agent_id": "panel-agent-1", "severity": "info", "finding": "Reasoning is thin but consistent."}],
        "summary": "Panel responses look sound.",
    }
)


class _FakeProvider:
    """Routes to a QA-precheck response or the stage's own response based on
    which prompt is actually being asked, exactly like a single monkeypatch
    of `get_provider` must serve both calls Agent.run() makes."""

    def __init__(self, main_response_text: str):
        self.main_response_text = main_response_text

    def complete(self, messages, *, model, temperature, max_tokens, top_p=1.0, seed=None, **extra):
        prompt = messages[-1]["content"]
        text = _QA_RESPONSE if "confirm your configuration" in prompt else self.main_response_text
        return ProviderResponse(text=text, model=model, finish_reason="stop")


def _write_prompt_template(tmp_path: Path) -> Path:
    path = tmp_path / "system_prompt.txt"
    path.write_text("Role: {role}\n{role_description}\n", encoding="utf-8")
    return path


def _make_survey(tmp_path: Path, pipeline_config: dict) -> SurveyConfig:
    survey_dir = tmp_path / "survey"
    agents_dir = survey_dir / "agents"
    agents_dir.mkdir(parents=True)
    pipeline_dir = survey_dir / "pipeline_agents"
    pipeline_dir.mkdir(parents=True)

    (survey_dir / "survey.yaml").write_text("id: test-survey\ntitle: Test Survey\ninstrument: bwm\n", encoding="utf-8")

    panel_card_path = agents_dir / "panel-agent-1.json"
    new_card(
        agent_id="panel-agent-1",
        role="Data Engineer",
        role_description="A test persona.",
        system_prompt_template=str(_write_prompt_template(tmp_path)),
        model=ModelSpec(provider="ollama", name="test-model"),
        did_seed="test-seed",
    ).write(panel_card_path)

    setup_fixer_card_path = pipeline_dir / "setup-fixer.json"
    new_card(
        agent_id="setup-fixer",
        role="setup reviewer",
        role_description="A meticulous methodology reviewer.",
        system_prompt_template=str(_write_prompt_template(tmp_path)),
        model=ModelSpec(provider="ollama", name="test-model"),
        did_seed="test-seed",
        instrument="setup_review",
    ).write(setup_fixer_card_path)

    response_reviewer_card_path = pipeline_dir / "response-reviewer.json"
    new_card(
        agent_id="response-reviewer",
        role="response reviewer",
        role_description="A careful second-pass critic.",
        system_prompt_template=str(_write_prompt_template(tmp_path)),
        model=ModelSpec(provider="ollama", name="test-model"),
        did_seed="test-seed",
        instrument="response_review",
    ).write(response_reviewer_card_path)

    return SurveyConfig(
        id="test-survey",
        title="Test Survey",
        instrument="bwm",
        instrument_params={"dimensions": ["A", "B"]},
        weighting={},
        root=survey_dir,
        agent_cards=[panel_card_path],
        pipeline=pipeline_config,
    )


def test_run_setup_review_returns_none_when_not_configured(tmp_path):
    survey = _make_survey(tmp_path, pipeline_config={})
    storage = SurveyStorage(survey.root)
    assert pipeline.run_setup_review(survey, storage) is None


def test_run_response_review_returns_none_when_not_configured(tmp_path):
    survey = _make_survey(tmp_path, pipeline_config={})
    storage = SurveyStorage(survey.root)
    assert pipeline.run_response_review(survey, storage, [], codes=["A", "B"]) is None


def test_run_setup_review_produces_findings_via_a_real_child_spawn(tmp_path, monkeypatch):
    monkeypatch.setattr(agent_module, "get_provider", lambda name: _FakeProvider(_SETUP_REVIEW_RESPONSE))

    survey = _make_survey(tmp_path, pipeline_config={"setup_review": {"agent_card": "pipeline_agents/setup-fixer.json"}})
    storage = SurveyStorage(survey.root)

    result = pipeline.run_setup_review(survey, storage)

    assert "error" not in result
    assert result["findings"][0]["area"] == "dimensions"
    assert result["summary"] == "Mostly ready; one wording issue."

    # A genuine capability-attenuated child spawn, not a special-cased root
    # spawn: spawned_by names the pipeline-orchestrator parent, and the
    # lineage edge records the same parent/child DID pair.
    declaration = json.loads((storage.agent_dir("setup-fixer") / "spawn_declaration.json").read_text())
    assert declaration["spawned_by"] == "agent:pipeline-orchestrator"
    assert declaration["parent_did"] is not None
    edges = lineage._read(storage)
    assert any(
        e["child_agent_id"] == "setup-fixer" and e["parent_did"] == declaration["parent_did"] for e in edges
    )


def test_run_response_review_produces_findings_via_a_real_child_spawn(tmp_path, monkeypatch):
    monkeypatch.setattr(agent_module, "get_provider", lambda name: _FakeProvider(_RESPONSE_REVIEW_RESPONSE))

    survey = _make_survey(
        tmp_path, pipeline_config={"response_review": {"agent_card": "pipeline_agents/response-reviewer.json"}}
    )
    storage = SurveyStorage(survey.root)
    per_agent_detail = [
        {
            "agent_id": "panel-agent-1",
            "role": "Data Engineer",
            "answer": {"best": "A", "worst": "B"},
            "reasoning": "A clearly outranks B.",
        }
    ]

    result = pipeline.run_response_review(survey, storage, per_agent_detail, codes=["A", "B"])

    assert "error" not in result
    assert result["findings"][0]["agent_id"] == "panel-agent-1"

    declaration = json.loads((storage.agent_dir("response-reviewer") / "spawn_declaration.json").read_text())
    assert declaration["spawned_by"] == "agent:pipeline-orchestrator"


def test_run_setup_review_reports_error_without_raising_on_missing_card(tmp_path):
    survey = _make_survey(tmp_path, pipeline_config={"setup_review": {"agent_card": "pipeline_agents/does-not-exist.json"}})
    storage = SurveyStorage(survey.root)

    result = pipeline.run_setup_review(survey, storage)

    assert "error" in result


def test_pipeline_root_identity_is_deterministic_per_survey_id(tmp_path):
    survey_a = _make_survey(tmp_path, pipeline_config={})
    survey_a_again = SurveyConfig(**{**survey_a.__dict__})
    assert pipeline._pipeline_root_identity(survey_a).did == pipeline._pipeline_root_identity(survey_a_again).did
