"""End-to-end test of the Agent Library HTTP endpoints: create in the
library, list, assign a copy into a survey (materializing it with the same
identity), refuse a duplicate assign, delete. Uses FastAPI's TestClient
against a real (temp-directory) SURVEYS_ROOT/LIBRARY_ROOT rather than
mocking anything, since library.py's actual behaviour (404/409 handling,
path resolution) is exactly what would otherwise go unverified by the pure
unit tests elsewhere in this suite.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "web"))


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("SURVEYS_ROOT", str(tmp_path / "surveys"))
    monkeypatch.setenv("LIBRARY_ROOT", str(tmp_path / "agents_library"))
    # paths.py (and everything that did `from ..paths import ...`) binds
    # SURVEYS_ROOT/LIBRARY_ROOT at import time, so a fresh import per test
    # is required for the env vars above to actually take effect.
    for mod in list(sys.modules):
        if mod.startswith("backend"):
            del sys.modules[mod]

    from fastapi.testclient import TestClient

    from backend.main import app

    return TestClient(app)


def _agent_body(agent_id: str = "test-agent") -> dict:
    return {
        "agent_id": agent_id,
        "role": "Tester",
        "role_description": "A test persona.",
        "model": {"provider": "ollama", "name": "test-model"},
        "did_seed": "test-seed",
    }


def test_library_crud_and_assign_to_survey(client, tmp_path):
    survey_dir = tmp_path / "surveys" / "demo-survey"
    (survey_dir / "agents").mkdir(parents=True)
    (survey_dir / "survey.yaml").write_text("id: demo-survey\ntitle: Demo\ninstrument: bwm\n", encoding="utf-8")

    resp = client.post("/api/library/agents", json=_agent_body())
    assert resp.status_code == 200, resp.text
    card = resp.json()
    assert card["agent_id"] == "test-agent"
    assert card["did"]["id"].startswith("did:key:")

    resp = client.get("/api/library/agents")
    assert resp.status_code == 200
    assert [a["agent_id"] for a in resp.json()] == ["test-agent"]

    # duplicate create in the library itself is rejected
    resp = client.post("/api/library/agents", json=_agent_body())
    assert resp.status_code == 409

    resp = client.post("/api/library/agents/test-agent/assign/demo-survey")
    assert resp.status_code == 200, resp.text
    assigned = resp.json()
    assert assigned["did"]["id"] == card["did"]["id"]  # same identity, materialized copy
    assert (survey_dir / "agents" / "test-agent.json").exists()

    # a survey that already has this agent id refuses a second assign
    resp = client.post("/api/library/agents/test-agent/assign/demo-survey")
    assert resp.status_code == 409

    # assigning a library agent that doesn't exist 404s
    resp = client.post("/api/library/agents/does-not-exist/assign/demo-survey")
    assert resp.status_code == 404

    # assigning into a survey that doesn't exist 404s
    resp = client.post("/api/library/agents/test-agent/assign/no-such-survey")
    assert resp.status_code == 404

    resp = client.delete("/api/library/agents/test-agent")
    assert resp.status_code == 200
    resp = client.get("/api/library/agents")
    assert resp.json() == []

    # the survey-scoped copy is untouched by deleting the library original
    assert (survey_dir / "agents" / "test-agent.json").exists()
