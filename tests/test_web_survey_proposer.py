"""End-to-end test of POST /api/surveys/propose-concept against a real
FastAPI TestClient, with the LLM provider faked at the boundary."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "web"))


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("SURVEYS_ROOT", str(tmp_path / "surveys"))
    monkeypatch.setenv("LIBRARY_ROOT", str(tmp_path / "agents_library"))
    for mod in list(sys.modules):
        if mod.startswith("backend"):
            del sys.modules[mod]

    from fastapi.testclient import TestClient

    from backend.main import app

    return TestClient(app)


_FAKE_RESPONSE_TEXT = """{
  "title": "Cloud Migration Risk Weighting",
  "description": "Weighs the criteria that matter most for a cloud migration decision.",
  "instrument": "bwm",
  "instrument_justification": "Five criteria is moderate; BWM is efficient here.",
  "criteria": [
    {"code": "COST", "label": "Migration cost"},
    {"code": "SEC", "label": "Security posture"},
    {"code": "DOWN", "label": "Downtime risk"}
  ]
}"""


def test_propose_concept_returns_a_parsed_draft(client, monkeypatch):
    class _FakeProvider:
        def complete(self, messages, *, model, temperature, max_tokens, top_p=1.0, seed=None, **extra):
            class _R:
                text = _FAKE_RESPONSE_TEXT

            return _R()

    import agentic_survey.providers as providers_module

    monkeypatch.setattr(providers_module, "get_provider", lambda name: _FakeProvider())

    resp = client.post(
        "/api/surveys/propose-concept",
        json={"concept": "A study about cloud migration risk.", "provider": "ollama", "model": "mistral:7b"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["title"] == "Cloud Migration Risk Weighting"
    assert body["instrument"] == "bwm"
    assert len(body["criteria"]) == 3


def test_propose_concept_returns_502_on_unparseable_response(client, monkeypatch):
    class _FakeProvider:
        def complete(self, messages, *, model, temperature, max_tokens, top_p=1.0, seed=None, **extra):
            class _R:
                text = "I can't help with that."

            return _R()

    import agentic_survey.providers as providers_module

    monkeypatch.setattr(providers_module, "get_provider", lambda name: _FakeProvider())

    resp = client.post(
        "/api/surveys/propose-concept",
        json={"concept": "Something vague.", "provider": "ollama", "model": "mistral:7b"},
    )
    assert resp.status_code == 502
