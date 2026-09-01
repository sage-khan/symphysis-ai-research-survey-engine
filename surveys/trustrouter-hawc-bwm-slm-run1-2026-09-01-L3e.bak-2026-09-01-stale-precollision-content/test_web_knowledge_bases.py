"""End-to-end test of the reusable knowledge-base HTTP endpoints: create,
list, upload a file, list files, delete a file, delete the knowledge base.
Uses FastAPI's TestClient against a real (temp-directory) LIBRARY_ROOT."""

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


def test_create_list_upload_and_delete_knowledge_base(client):
    resp = client.post(
        "/api/knowledge-bases",
        json={"id": "blockchain-trust", "name": "Blockchain Trust", "description": "Trust and attack-resistance literature."},
    )
    assert resp.status_code == 200, resp.text
    kb = resp.json()
    assert kb["id"] == "blockchain-trust"
    assert kb["corpus_path"] == "agents_library/knowledge_bases/blockchain-trust"
    assert kb["file_count"] == 0

    resp = client.get("/api/knowledge-bases")
    assert resp.status_code == 200
    assert [k["id"] for k in resp.json()] == ["blockchain-trust"]

    resp = client.post(
        "/api/knowledge-bases/blockchain-trust/files",
        files={"file": ("rouhani2021.md", b"# Data trust framework\nReal cited content.", "text/markdown")},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["filename"] == "rouhani2021.md"

    resp = client.get("/api/knowledge-bases")
    assert resp.json()[0]["file_count"] == 1
    assert resp.json()[0]["files"][0]["filename"] == "rouhani2021.md"

    resp = client.delete("/api/knowledge-bases/blockchain-trust/files/rouhani2021.md")
    assert resp.status_code == 200
    assert client.get("/api/knowledge-bases").json()[0]["file_count"] == 0

    resp = client.delete("/api/knowledge-bases/blockchain-trust")
    assert resp.status_code == 200
    assert client.get("/api/knowledge-bases").json() == []


def test_create_duplicate_knowledge_base_rejected(client):
    body = {"id": "dup", "name": "Dup"}
    assert client.post("/api/knowledge-bases", json=body).status_code == 200
    resp = client.post("/api/knowledge-bases", json=body)
    assert resp.status_code == 409


def test_upload_to_unknown_knowledge_base_404s(client):
    resp = client.post(
        "/api/knowledge-bases/does-not-exist/files",
        files={"file": ("a.md", b"content", "text/markdown")},
    )
    assert resp.status_code == 404


def test_upload_rejects_unsupported_file_type(client):
    client.post("/api/knowledge-bases", json={"id": "kb1", "name": "KB1"})
    resp = client.post(
        "/api/knowledge-bases/kb1/files",
        files={"file": ("a.exe", b"content", "application/octet-stream")},
    )
    assert resp.status_code == 400
