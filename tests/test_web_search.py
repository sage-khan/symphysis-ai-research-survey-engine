import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentic_survey.tools import web_search


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


def test_raises_clearly_when_no_api_key(monkeypatch):
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    with pytest.raises(web_search.WebSearchError, match="TAVILY_API_KEY"):
        web_search.search("some query")


def test_returns_real_results_shape(monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")

    def fake_post(url, json=None, **kwargs):
        assert url == "https://api.tavily.com/search"
        assert json["api_key"] == "test-key"
        assert json["query"] == "wind turbine SCADA standards"
        return _FakeResponse(
            {
                "results": [
                    {"title": "IEC 61400", "url": "https://example.com/iec", "content": "Wind turbine standard."},
                    {"title": "SCADA overview", "url": "https://example.com/scada", "content": "SCADA systems."},
                ]
            }
        )

    monkeypatch.setattr(web_search.requests, "post", fake_post)
    results = web_search.search("wind turbine SCADA standards", top_k=5)
    assert len(results) == 2
    assert results[0].title == "IEC 61400"
    assert results[0].url == "https://example.com/iec"


def test_truncates_to_top_k(monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")

    def fake_post(url, json=None, **kwargs):
        return _FakeResponse({"results": [{"title": f"r{i}", "url": "u", "content": "c"} for i in range(10)]})

    monkeypatch.setattr(web_search.requests, "post", fake_post)
    results = web_search.search("query", top_k=3)
    assert len(results) == 3


def test_raises_on_request_failure(monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")

    def fake_post(url, json=None, **kwargs):
        import requests

        raise requests.ConnectionError("network down")

    monkeypatch.setattr(web_search.requests, "post", fake_post)
    with pytest.raises(web_search.WebSearchError, match="network down"):
        web_search.search("query")


def test_search_as_dicts_shape(monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")

    def fake_post(url, json=None, **kwargs):
        return _FakeResponse({"results": [{"title": "t", "url": "u", "content": "c"}]})

    monkeypatch.setattr(web_search.requests, "post", fake_post)
    results = web_search.search_as_dicts("query")
    assert results == [{"title": "t", "url": "u", "content": "c"}]
