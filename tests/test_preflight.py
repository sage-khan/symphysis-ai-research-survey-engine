import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from symphysis import preflight
from symphysis.agent_card import GuardrailsSpec, ModelSpec, PermissionsSpec, RagSpec, SamplingSpec, new_card
from symphysis.config import load_survey_config

import yaml


class _FakeResponse:
    def __init__(self, json_data, status=200):
        self._json = json_data
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            import requests
            raise requests.HTTPError(f"status {self.status_code}")

    def json(self):
        return self._json


def test_check_ollama_ok_when_models_present(monkeypatch):
    def fake_get(url, timeout=None, **kwargs):
        assert url == "http://localhost:11434/api/tags"
        return _FakeResponse({"models": [{"name": "qwen2.5:14b"}, {"name": "llama3"}]})

    monkeypatch.setattr(preflight.requests, "get", fake_get)
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
    status = preflight.check_ollama()
    assert status.ok
    assert status.models == ["llama3", "qwen2.5:14b"]


def test_check_ollama_fails_when_unreachable(monkeypatch):
    def fake_get(url, timeout=None, **kwargs):
        import requests
        raise requests.ConnectionError("refused")

    monkeypatch.setattr(preflight.requests, "get", fake_get)
    status = preflight.check_ollama(base_url="http://localhost:11434")
    assert not status.ok
    assert "unreachable" in status.detail


def test_check_ollama_fails_when_no_models_pulled(monkeypatch):
    def fake_get(url, timeout=None, **kwargs):
        return _FakeResponse({"models": []})

    monkeypatch.setattr(preflight.requests, "get", fake_get)
    status = preflight.check_ollama(base_url="http://localhost:11434")
    assert not status.ok
    assert "no models pulled" in status.detail


def test_check_hosted_provider_ok_when_key_set(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    status = preflight.check_hosted_provider("anthropic")
    assert status.ok


def test_check_hosted_provider_fails_when_key_unset(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    status = preflight.check_hosted_provider("openai")
    assert not status.ok
    assert "OPENAI_API_KEY" in status.detail


def test_check_manual_is_always_ok():
    status = preflight.check_manual()
    assert status.ok


def test_check_providers_deduplicates_and_preserves_order(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")

    def fake_get(url, timeout=None, **kwargs):
        return _FakeResponse({"models": [{"name": "m"}]})

    monkeypatch.setattr(preflight.requests, "get", fake_get)
    results = preflight.check_providers(["ollama", "anthropic", "ollama", "manual"])
    assert [r.provider for r in results] == ["ollama", "anthropic", "manual"]


def test_check_survey_providers_covers_every_agent(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")

    def fake_get(url, timeout=None, **kwargs):
        return _FakeResponse({"models": [{"name": "m"}]})

    monkeypatch.setattr(preflight.requests, "get", fake_get)

    survey_dir = tmp_path / "preflight-test"
    (survey_dir / "agents").mkdir(parents=True)
    (survey_dir / "survey.yaml").write_text(
        yaml.dump({
            "id": "preflight-test", "title": "Preflight test", "instrument": "bwm",
            "instrument_params": {"dimensions": ["A", "B"], "dimension_labels": {}},
            "weighting": {},
        }),
        encoding="utf-8",
    )
    prompt_template = tmp_path / "system_prompt.txt"
    prompt_template.write_text("Role: {role}\n{role_description}\n", encoding="utf-8")

    for agent_id, provider in [("a1", "ollama"), ("a2", "anthropic")]:
        card = new_card(
            agent_id=agent_id, role="Reviewer", role_description="x",
            system_prompt_template=str(prompt_template),
            model=ModelSpec(provider=provider, name="m"),
            rag=RagSpec(enabled=False), sampling=SamplingSpec(),
            permissions=PermissionsSpec(), guardrails=GuardrailsSpec(),
            did_seed="preflight-test-seed",
        )
        card.write(survey_dir / "agents" / f"{agent_id}.json")

    survey = load_survey_config(survey_dir)
    results = preflight.check_survey_providers(survey)
    assert {r.provider for r in results} == {"ollama", "anthropic"}
    assert all(r.ok for r in results)


def test_check_survey_providers_skips_a_broken_card(tmp_path):
    survey_dir = tmp_path / "preflight-broken-test"
    (survey_dir / "agents").mkdir(parents=True)
    (survey_dir / "survey.yaml").write_text(
        yaml.dump({
            "id": "preflight-broken-test", "title": "x", "instrument": "bwm",
            "instrument_params": {"dimensions": ["A", "B"], "dimension_labels": {}},
            "weighting": {},
        }),
        encoding="utf-8",
    )
    (survey_dir / "agents" / "broken.json").write_text("{not valid json", encoding="utf-8")

    survey = load_survey_config(survey_dir)
    results = preflight.check_survey_providers(survey)
    assert results == []


def test_status_to_dict_shape():
    status = preflight.ProviderStatus(provider="ollama", ok=True, detail="fine", models=["a"])
    assert preflight.status_to_dict(status) == {"provider": "ollama", "ok": True, "detail": "fine", "models": ["a"]}
