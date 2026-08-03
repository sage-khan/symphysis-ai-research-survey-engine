"""End-to-end test of the integrity-manifest HTTP endpoints against a real
(temp-directory) SURVEYS_ROOT, following the same TestClient pattern as
test_web_library.py."""

import sys
from pathlib import Path

import pytest
import yaml

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

    return TestClient(app), tmp_path


def _make_survey_with_manifest(tmp_path: Path, survey_id: str) -> Path:
    from agentic_survey import integrity

    d = tmp_path / "surveys" / survey_id
    d.mkdir(parents=True)
    (d / "survey.yaml").write_text(yaml.safe_dump({"id": survey_id, "title": "T"}), encoding="utf-8")
    (d / "report").mkdir()
    (d / "report" / "report.md").write_text("# Report\n", encoding="utf-8")
    integrity.write_manifest(d)
    return d


def test_get_integrity_manifest_404s_without_a_run(client):
    c, tmp_path = client
    d = tmp_path / "surveys" / "no-manifest-yet"
    d.mkdir(parents=True)
    (d / "survey.yaml").write_text(yaml.safe_dump({"id": "no-manifest-yet"}), encoding="utf-8")
    resp = c.get("/api/surveys/no-manifest-yet/integrity")
    assert resp.status_code == 404


def test_get_integrity_manifest_returns_it_after_a_run(client):
    c, tmp_path = client
    _make_survey_with_manifest(tmp_path, "has-manifest")
    resp = c.get("/api/surveys/has-manifest/integrity")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["root_hash"]) == 64
    assert body["file_count"] >= 1


def test_verify_integrity_passes_when_untouched(client):
    c, tmp_path = client
    _make_survey_with_manifest(tmp_path, "untouched")
    resp = c.get("/api/surveys/untouched/verify-integrity")
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


def test_verify_integrity_fails_after_a_file_is_altered(client):
    c, tmp_path = client
    d = _make_survey_with_manifest(tmp_path, "altered")
    (d / "report" / "report.md").write_text("# Tampered report\n", encoding="utf-8")
    resp = c.get("/api/surveys/altered/verify-integrity")
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is False
    assert "report/report.md" in body["changed"]
