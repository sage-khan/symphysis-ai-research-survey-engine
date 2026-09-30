"""Real web search via two self-hosted, fully open-source services, rather
than a paid third-party API: SearXNG for discovery (query -> candidate
URLs + snippets) and Crawl4AI for extraction (URL -> clean, full-page
markdown), per this project's open-source-by-default rule
(`.claude/rules/gitops.md`).

This replaces an earlier Tavily-backed implementation that depended on a
paid, closed-source API and a `TAVILY_API_KEY` that was never actually
configured in any real deployment of this app, leaving the tool dead
weight. Both services are Docker-deployable, Apache/AGPL licensed, and
need no API key.

Base URLs come from `SEARXNG_BASE_URL` / `CRAWL4AI_BASE_URL` environment
variables, else `config/defaults.yaml`'s `web_search` section (see
`app_config.web_search_config()`), else a hardcoded default assuming both
run as sibling services on the same Docker Compose network (see
`docker-compose.yml`).

Two failure classes are handled differently, on purpose:
- SearXNG (the discovery step) unreachable or misconfigured: nothing to
  search over at all, so `search()` raises `WebSearchError` immediately,
  exactly like the old Tavily implementation raised on any failure.
- Crawl4AI (the extraction step) unreachable, or a specific URL's
  extraction failing: each affected result falls back to SearXNG's own
  snippet rather than being dropped, since a search engine's snippet is
  still real, non-fabricated content, just shorter than a full-page
  extraction. Only if Crawl4AI never succeeds for ANY candidate does this
  matter in practice; a transient single-URL failure shouldn't take down
  results that did extract successfully.

Callers must not substitute a plausible-looking fallback of their own; an
agent that can't search should say so in its guardrail-visible trace, not
silently proceed as if it had real results.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, List

import requests

_TIMEOUT = 15.0
_EXTRACT_TIMEOUT = 30.0  # Crawl4AI drives a real headless browser; slower than a plain HTTP fetch.

_DEFAULT_SEARXNG_BASE_URL = "http://searxng:8080"
_DEFAULT_CRAWL4AI_BASE_URL = "http://crawl4ai:11235"


class WebSearchError(Exception):
    pass


@dataclass
class SearchResult:
    title: str
    url: str
    content: str


def _config() -> Dict[str, Any]:
    try:
        from ..app_config import web_search_config

        return web_search_config()
    except Exception:  # noqa: BLE001 - app_config itself failing to import must not break a URL lookup
        return {}


def _searxng_base_url() -> str:
    return os.environ.get("SEARXNG_BASE_URL") or _config().get("searxng_base_url", _DEFAULT_SEARXNG_BASE_URL)


def _crawl4ai_base_url() -> str:
    return os.environ.get("CRAWL4AI_BASE_URL") or _config().get("crawl4ai_base_url", _DEFAULT_CRAWL4AI_BASE_URL)


def _discover(query: str, top_k: int) -> List[Dict[str, str]]:
    """Query SearXNG's JSON API for `top_k` candidate results, each with a
    title, url, and short snippet. Raises WebSearchError if SearXNG is
    unreachable, misconfigured (JSON format not enabled in its own
    settings.yml), or returns something that doesn't parse as JSON."""
    base_url = _searxng_base_url()
    try:
        resp = requests.get(
            f"{base_url}/search",
            params={"q": query, "format": "json"},
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise WebSearchError(f"SearXNG search request failed ({base_url}): {exc}") from exc

    try:
        data = resp.json()
    except ValueError as exc:
        raise WebSearchError(
            f"SearXNG at {base_url} did not return JSON; is 'json' enabled under settings.yml's "
            f"search.formats?"
        ) from exc

    results = data.get("results", [])
    return [
        {"title": r.get("title", ""), "url": r.get("url", ""), "content": r.get("content", "")}
        for r in results[:top_k]
        if r.get("url")
    ]


def _extract_markdown(url: str) -> str | None:
    """Fetch `url` via Crawl4AI and return its clean markdown content, or
    None if extraction failed for this specific URL (caller falls back to
    the SearXNG snippet). Does not raise: a single hard-to-crawl page is
    not the same failure as the whole extraction service being down."""
    base_url = _crawl4ai_base_url()
    try:
        resp = requests.post(
            f"{base_url}/crawl",
            json={"urls": [url]},
            timeout=_EXTRACT_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError):
        return None

    results = data.get("results") or []
    if not results:
        return None
    entry = results[0]
    if entry.get("success") is False:
        return None
    markdown = entry.get("markdown")
    if isinstance(markdown, dict):
        # Some Crawl4AI versions return a structured markdown object
        # (raw_markdown, fit_markdown, ...) instead of a plain string.
        markdown = markdown.get("raw_markdown") or markdown.get("fit_markdown")
    return markdown or None


def search(query: str, top_k: int = 5) -> List[SearchResult]:
    candidates = _discover(query, top_k)
    results: List[SearchResult] = []
    for c in candidates:
        extracted = _extract_markdown(c["url"])
        content = extracted if extracted else c["content"]
        results.append(SearchResult(title=c["title"], url=c["url"], content=content))
    return results


def search_as_dicts(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    return [{"title": r.title, "url": r.url, "content": r.content} for r in search(query, top_k)]
