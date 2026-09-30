"""End-to-end test of GET /api/surveys/{id}/preflight against a real
(temp-directory) SURVEYS_ROOT, following the same TestClient pattern as
test_web_integrity.py."""

import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "web"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("SURVEYS_ROOT", str(tmp_path / "surveys"))
    monkeypatch.setenv("LIBRARY_ROOT", str(tmp_path / "agents_library"))
    for mod in list(sys.modules):
        if mod.startswith("backend"):
            del sys.modules[mod]

    from fastapi.testclient import TestClient

    from backend.main import app

    return TestClient(app), tmp_path


def _make_survey(tmp_path: Path, survey_id: str) -> Path:
    d = tmp_path / "surveys" / survey_id
    (d / "agents").mkdir(parents=True)
    (d / "survey.yaml").write_text(
        yaml.safe_dump({
            "id": survey_id, "title": "T", "instrument": "bwm",
            "instrument_params": {"dimensions": ["A", "B"], "dimension_labels": {}},
            "weighting": {},
        }),
        encoding="utf-8",
    )
    return d


def _write_card(d: Path, agent_id: str, provider: str) -> None:
    from symphysis.agent_card import GuardrailsSpec, ModelSpec, PermissionsSpec, RagSpec, SamplingSpec, new_card

    prompt_template = d / "system_prompt.txt"
    if not prompt_template.exists():
        prompt_template.write_text("Role: {role}\n{role_description}\n", encoding="utf-8")
    card = new_card(
        agent_id=agent_id, role="Reviewer", role_description="x",
        system_prompt_template=str(prompt_template),
        model=ModelSpec(provider=provider, name="m"),
        rag=RagSpec(enabled=False), sampling=SamplingSpec(),
        permissions=PermissionsSpec(), guardrails=GuardrailsSpec(),
        did_seed="web-preflight-test-seed",
    )
    card.write(d / "agents" / f"{agent_id}.json")


def test_preflight_404s_for_an_unknown_survey(client):
    c, _ = client
    resp = c.get("/api/surveys/no-such-survey/preflight")
    assert resp.status_code == 404


def test_preflight_reports_ok_for_manual_only_agents(client):
    c, tmp_path = client
    d = _make_survey(tmp_path, "preflight-manual")
    _write_card(d, "a1", "manual")

    resp = c.get("/api/surveys/preflight-manual/preflight")
    assert resp.status_code == 200
    body = resp.json()
    assert body["all_ok"] is True
    assert body["providers"] == [{"provider": "manual", "ok": True, "detail": "human-paste workflow, no endpoint to check", "models": None}]


def test_preflight_reports_failure_for_an_unset_hosted_api_key(client, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    c, tmp_path = client
    d = _make_survey(tmp_path, "preflight-anthropic")
    _write_card(d, "a1", "anthropic")

    resp = c.get("/api/surveys/preflight-anthropic/preflight")
    assert resp.status_code == 200
    body = resp.json()
    assert body["all_ok"] is False
    assert body["providers"][0]["provider"] == "anthropic"
    assert body["providers"][0]["ok"] is False


def test_preflight_deduplicates_across_multiple_agents_on_the_same_provider(client):
    c, tmp_path = client
    d = _make_survey(tmp_path, "preflight-dedupe")
    _write_card(d, "a1", "manual")
    _write_card(d, "a2", "manual")

    resp = c.get("/api/surveys/preflight-dedupe/preflight")
    body = resp.json()
    assert len(body["providers"]) == 1
