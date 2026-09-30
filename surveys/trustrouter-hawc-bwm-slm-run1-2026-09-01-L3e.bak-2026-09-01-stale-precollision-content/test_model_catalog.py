import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "web"))

from backend import model_catalog


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


def test_ollama_models_lists_actual_tags(monkeypatch):
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434")

    def fake_get(url, **kwargs):
        assert url == "http://localhost:11434/api/tags"
        return _FakeResponse({"models": [{"name": "mistral:7b"}, {"name": "qwen2.5:14b"}]})

    monkeypatch.setattr(model_catalog.requests, "get", fake_get)
    result = model_catalog.list_models("ollama")
    assert result == {"models": ["mistral:7b", "qwen2.5:14b"], "error": None}


def test_openai_compatible_provider_without_key_returns_error(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    result = model_catalog.list_models("groq")
    assert result["models"] == []
    assert "GROQ_API_KEY" in result["error"]


def test_openai_compatible_provider_with_key_lists_models(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")

    def fake_get(url, headers=None, **kwargs):
        assert url == "https://api.groq.com/openai/v1/models"
        assert headers["Authorization"] == "Bearer test-key"
        return _FakeResponse({"data": [{"id": "llama-3.3-70b"}, {"id": "mixtral-8x7b"}]})

    monkeypatch.setattr(model_catalog.requests, "get", fake_get)
    result = model_catalog.list_models("groq")
    assert result == {"models": ["llama-3.3-70b", "mixtral-8x7b"], "error": None}


def test_anthropic_uses_x_api_key_header(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "ant-key")

    def fake_get(url, headers=None, **kwargs):
        assert url == "https://api.anthropic.com/v1/models"
        assert headers["x-api-key"] == "ant-key"
        return _FakeResponse({"data": [{"id": "claude-sonnet-5"}]})

    monkeypatch.setattr(model_catalog.requests, "get", fake_get)
    result = model_catalog.list_models("anthropic")
    assert result == {"models": ["claude-sonnet-5"], "error": None}


def test_manual_provider_has_no_list_but_no_crash():
    result = model_catalog.list_models("manual")
    assert result["models"] == []
    assert result["error"] is not None


def test_unknown_provider_returns_error_not_exception():
    result = model_catalog.list_models("not-a-real-provider")
    assert result["models"] == []
    assert "Unknown provider" in result["error"]


def test_unreachable_provider_degrades_to_error(monkeypatch):
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434")

    def fake_get(url, **kwargs):
        import requests

        raise requests.ConnectionError("connection refused")

    monkeypatch.setattr(model_catalog.requests, "get", fake_get)
    result = model_catalog.list_models("ollama")
    assert result["models"] == []
    assert "connection refused" in result["error"]


def test_model_is_available_true_for_known_model(monkeypatch):
    monkeypatch.setattr(model_catalog, "list_models", lambda p: {"models": ["real-model"], "error": None})
    assert model_catalog.model_is_available("ollama", "real-model") is True
    assert model_catalog.model_is_available("ollama", "hallucinated-model") is False


def test_model_is_available_gives_benefit_of_the_doubt_when_catalog_unreachable(monkeypatch):
    monkeypatch.setattr(model_catalog, "list_models", lambda p: {"models": [], "error": "unreachable"})
    assert model_catalog.model_is_available("ollama", "anything") is True
