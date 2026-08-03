"""Tests for Agent's context-gathering: the shared survey-level knowledge
repo (auto-detected, no per-agent flag) and the web_search tool (only when
granted via card.tools, degrades gracefully on failure). RAG-over-a-
dedicated-corpus is already covered elsewhere; this file is about how the
three context sources combine.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentic_survey import agent as agent_module
from agentic_survey.agent import Agent, _has_retrievable_content
from agentic_survey.agent_card import ModelSpec, new_card
from agentic_survey.storage import SurveyStorage
from agentic_survey.tools.web_search import WebSearchError


def _make_agent(tmp_path: Path, agent_id: str = "test-agent", tools=None) -> Agent:
    survey_dir = tmp_path / "survey"
    survey_dir.mkdir(parents=True, exist_ok=True)
    card_path = survey_dir / "agents" / f"{agent_id}.json"
    card_path.parent.mkdir(parents=True, exist_ok=True)
    card = new_card(
        agent_id=agent_id,
        role="Tester",
        role_description="A test persona.",
        system_prompt_template=str(_write_prompt_template(tmp_path)),
        model=ModelSpec(provider="ollama", name="test-model"),
        tools=tools or [],
        did_seed="test-seed",
    )
    card.write(card_path)
    storage = SurveyStorage(survey_dir)
    return Agent(card, card_path, storage)


def _write_prompt_template(tmp_path: Path) -> Path:
    path = tmp_path / "system_prompt.txt"
    path.write_text("Role: {role}\n{role_description}\n", encoding="utf-8")
    return path


def test_has_retrievable_content_false_for_missing_or_empty_dir(tmp_path):
    assert _has_retrievable_content(tmp_path / "does-not-exist") is False
    empty = tmp_path / "empty"
    empty.mkdir()
    assert _has_retrievable_content(empty) is False


def test_has_retrievable_content_true_when_md_or_txt_present(tmp_path):
    d = tmp_path / "has-content"
    d.mkdir()
    (d / "notes.md").write_text("some content", encoding="utf-8")
    assert _has_retrievable_content(d) is True


def test_agent_picks_up_shared_knowledge_repo_with_no_per_agent_flag(tmp_path):
    agent = _make_agent(tmp_path)
    knowledge_dir = agent.storage.root / "knowledge_repo"
    knowledge_dir.mkdir()
    (knowledge_dir / "background.md").write_text(
        "Wind turbines require structural health monitoring for blade fatigue.", encoding="utf-8"
    )
    # Re-instantiate: the retriever is built in __init__, so it needs the
    # file to exist before construction (matches how a real run works:
    # the knowledge repo is uploaded before a survey run starts).
    agent2 = _make_agent(tmp_path, agent_id="test-agent-2")
    chunks = agent2._context_chunks("structural health monitoring")
    assert any("shared knowledge" in c for c in chunks)
    assert any("blade fatigue" in c for c in chunks)


def test_web_search_not_called_without_tool_grant(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(agent_module, "search_as_dicts", lambda q, top_k=5: calls.append(q) or [])
    agent = _make_agent(tmp_path, tools=[])
    chunks = agent._context_chunks("some query")
    assert calls == []
    assert chunks == []


def test_web_search_called_when_tool_granted(tmp_path, monkeypatch):
    monkeypatch.setattr(
        agent_module,
        "search_as_dicts",
        lambda q, top_k=5: [{"title": "IEC 61400", "url": "https://example.com", "content": "wind turbine standard"}],
    )
    agent = _make_agent(tmp_path, tools=["web_search"])
    chunks = agent._context_chunks("wind turbine standards")
    assert any("IEC 61400" in c and "wind turbine standard" in c for c in chunks)


def test_web_search_failure_degrades_gracefully_and_is_logged(tmp_path, monkeypatch):
    def raise_error(q, top_k=5):
        raise WebSearchError("TAVILY_API_KEY is not set")

    monkeypatch.setattr(agent_module, "search_as_dicts", raise_error)
    agent = _make_agent(tmp_path, tools=["web_search"])
    chunks = agent._context_chunks("some query")
    assert chunks == []  # degrades to no results, does not raise

    conversation = (agent.storage.agent_dir(agent.card.agent_id) / "conversation.jsonl").read_text(encoding="utf-8")
    assert "web_search" in conversation
    assert "TAVILY_API_KEY" in conversation
