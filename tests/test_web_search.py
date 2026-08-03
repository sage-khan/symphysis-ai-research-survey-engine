import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from symphysis.tools import web_search


class _FakeResponse:
    def __init__(self, json_data, status=200, raise_json_error=False):
        self._json = json_data
        self.status_code = status
        self._raise_json_error = raise_json_error

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests_HTTPError(f"status {self.status_code}")

    def json(self):
        if self._raise_json_error:
            raise ValueError("not JSON")
        return self._json


def requests_HTTPError(msg):
    import requests

    return requests.HTTPError(msg)


@pytest.fixture(autouse=True)
def _base_urls(monkeypatch):
    monkeypatch.setenv("SEARXNG_BASE_URL", "http://searxng-test:8080")
    monkeypatch.setenv("CRAWL4AI_BASE_URL", "http://crawl4ai-test:11235")


def test_search_discovers_via_searxng_and_extracts_via_crawl4ai(monkeypatch):
    def fake_get(url, params=None, **kwargs):
        assert url == "http://searxng-test:8080/search"
        assert params == {"q": "wind turbine SCADA standards", "format": "json"}
        return _FakeResponse({
            "results": [
                {"title": "IEC 61400", "url": "https://example.com/iec", "content": "snippet a"},
                {"title": "SCADA overview", "url": "https://example.com/scada", "content": "snippet b"},
            ]
        })

    def fake_post(url, json=None, **kwargs):
        assert url == "http://crawl4ai-test:11235/crawl"
        target = json["urls"][0]
        return _FakeResponse({
            "results": [{"url": target, "success": True, "markdown": f"# full page for {target}"}]
        })

    monkeypatch.setattr(web_search.requests, "get", fake_get)
    monkeypatch.setattr(web_search.requests, "post", fake_post)

    results = web_search.search("wind turbine SCADA standards", top_k=5)
    assert len(results) == 2
    assert results[0].title == "IEC 61400"
    assert results[0].url == "https://example.com/iec"
    assert results[0].content == "# full page for https://example.com/iec"


def test_search_falls_back_to_snippet_when_extraction_fails_for_one_url(monkeypatch):
    def fake_get(url, params=None, **kwargs):
        return _FakeResponse({
            "results": [{"title": "t", "url": "https://example.com/x", "content": "the snippet"}]
        })

    def fake_post(url, json=None, **kwargs):
        raise __import__("requests").ConnectionError("crawl4ai down")

    monkeypatch.setattr(web_search.requests, "get", fake_get)
    monkeypatch.setattr(web_search.requests, "post", fake_post)

    results = web_search.search("query")
    assert len(results) == 1
    assert results[0].content == "the snippet"


def test_search_falls_back_to_snippet_when_crawl_reports_failure(monkeypatch):
    def fake_get(url, params=None, **kwargs):
        return _FakeResponse({"results": [{"title": "t", "url": "https://example.com/x", "content": "the snippet"}]})

    def fake_post(url, json=None, **kwargs):
        return _FakeResponse({"results": [{"url": "https://example.com/x", "success": False}]})

    monkeypatch.setattr(web_search.requests, "get", fake_get)
    monkeypatch.setattr(web_search.requests, "post", fake_post)

    results = web_search.search("query")
    assert results[0].content == "the snippet"


def test_search_handles_structured_markdown_response(monkeypatch):
    def fake_get(url, params=None, **kwargs):
        return _FakeResponse({"results": [{"title": "t", "url": "https://example.com/x", "content": "snippet"}]})

    def fake_post(url, json=None, **kwargs):
        return _FakeResponse({
            "results": [{"url": "https://example.com/x", "success": True,
                         "markdown": {"raw_markdown": "structured markdown body"}}]
        })

    monkeypatch.setattr(web_search.requests, "get", fake_get)
    monkeypatch.setattr(web_search.requests, "post", fake_post)

    results = web_search.search("query")
    assert results[0].content == "structured markdown body"


def test_search_raises_when_searxng_is_unreachable(monkeypatch):
    def fake_get(url, params=None, **kwargs):
        raise __import__("requests").ConnectionError("searxng down")

    monkeypatch.setattr(web_search.requests, "get", fake_get)
    with pytest.raises(web_search.WebSearchError, match="SearXNG"):
        web_search.search("query")


def test_search_raises_when_searxng_json_format_is_not_enabled(monkeypatch):
    def fake_get(url, params=None, **kwargs):
        return _FakeResponse({}, raise_json_error=True)

    monkeypatch.setattr(web_search.requests, "get", fake_get)
    with pytest.raises(web_search.WebSearchError, match="did not return JSON"):
        web_search.search("query")


def test_search_ignores_a_result_with_no_url(monkeypatch):
    def fake_get(url, params=None, **kwargs):
        return _FakeResponse({"results": [{"title": "no url", "content": "x"}]})

    monkeypatch.setattr(web_search.requests, "get", fake_get)
    results = web_search.search("query")
    assert results == []


def test_search_truncates_to_top_k(monkeypatch):
    def fake_get(url, params=None, **kwargs):
        return _FakeResponse({
            "results": [{"title": f"r{i}", "url": f"https://example.com/{i}", "content": "c"} for i in range(10)]
        })

    def fake_post(url, json=None, **kwargs):
        target = json["urls"][0]
        return _FakeResponse({"results": [{"url": target, "success": True, "markdown": "full"}]})

    monkeypatch.setattr(web_search.requests, "get", fake_get)
    monkeypatch.setattr(web_search.requests, "post", fake_post)

    results = web_search.search("query", top_k=3)
    assert len(results) == 3


def test_search_as_dicts_shape(monkeypatch):
    def fake_get(url, params=None, **kwargs):
        return _FakeResponse({"results": [{"title": "t", "url": "https://example.com/x", "content": "c"}]})

    def fake_post(url, json=None, **kwargs):
        return _FakeResponse({"results": [{"url": "https://example.com/x", "success": True, "markdown": "full"}]})

    monkeypatch.setattr(web_search.requests, "get", fake_get)
    monkeypatch.setattr(web_search.requests, "post", fake_post)

    results = web_search.search_as_dicts("query")
    assert results == [{"title": "t", "url": "https://example.com/x", "content": "full"}]


def test_base_urls_default_to_config_when_no_env_var(monkeypatch):
    monkeypatch.delenv("SEARXNG_BASE_URL", raising=False)
    monkeypatch.delenv("CRAWL4AI_BASE_URL", raising=False)
    assert web_search._searxng_base_url() == web_search._DEFAULT_SEARXNG_BASE_URL
    assert web_search._crawl4ai_base_url() == web_search._DEFAULT_CRAWL4AI_BASE_URL
