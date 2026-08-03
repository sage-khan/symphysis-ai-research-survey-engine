"""Real web search via the Tavily API (https://tavily.com), which is built
specifically for LLM-agent tool use: a single POST with a query returns a
short list of {title, url, content} results, no scraping or HTML parsing
needed on this side.

Requires TAVILY_API_KEY (Settings -> Config, "Web search" section, or the
environment variable directly). If it's not set, or the request fails,
`search()` raises `WebSearchError` -- callers must not substitute a
plausible-looking fallback; an agent that can't search should say so in its
guardrail-visible trace, not silently proceed as if it had real results.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, List

import requests

_ENDPOINT = "https://api.tavily.com/search"
_TIMEOUT = 15.0


class WebSearchError(Exception):
    pass


@dataclass
class SearchResult:
    title: str
    url: str
    content: str


def search(query: str, top_k: int = 5) -> List[SearchResult]:
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        raise WebSearchError("TAVILY_API_KEY is not set -- configure it in Settings before granting an agent web_search.")

    try:
        resp = requests.post(
            _ENDPOINT,
            json={"api_key": api_key, "query": query, "max_results": top_k},
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise WebSearchError(f"Tavily search request failed: {exc}") from exc

    data = resp.json()
    results = [
        SearchResult(title=r.get("title", ""), url=r.get("url", ""), content=r.get("content", ""))
        for r in data.get("results", [])
    ]
    return results[:top_k]


def search_as_dicts(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    return [{"title": r.title, "url": r.url, "content": r.content} for r in search(query, top_k)]
