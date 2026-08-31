"""Tests for tools/registry.py: build_registry() wraps the SAME retriever
instances Agent.__init__ already built, with a real (TF-IDF fallback, no
network/embedding-model dependency) corpus, not a mock retriever."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from symphysis.agent import Agent
from symphysis.agent_card import ModelSpec, PermissionsSpec, RagSpec, new_card
from symphysis.audit.logger import SurveyStorage
from symphysis.tools.registry import build_registry
from symphysis.tools.web_search import WebSearchError


def _write_prompt_template(tmp_path: Path) -> Path:
    path = tmp_path / "system_prompt.txt"
    path.write_text("Role: {role}\n{role_description}\n", encoding="utf-8")
    return path


def _make_agent(tmp_path: Path, agent_id: str = "registry-test-agent", **card_kwargs) -> Agent:
    survey_dir = tmp_path / "survey"
    card_path = survey_dir / "agents" / f"{agent_id}.json"
    card_path.parent.mkdir(parents=True, exist_ok=True)
    card = new_card(
        agent_id=agent_id,
        role="Data Engineer",
        role_description="A test persona.",
        system_prompt_template=str(_write_prompt_template(tmp_path)),
        model=ModelSpec(provider="ollama", name="test-model"),
        did_seed="test-seed",
        **card_kwargs,
    )
    card.write(card_path)
    storage = SurveyStorage(survey_dir)
    return Agent(card, card_path, storage)


def test_no_rag_no_web_search_only_registers_citation_verify(tmp_path):
    agent = _make_agent(tmp_path)
    registry = build_registry(agent)
    assert set(registry) == {"citation_verify"}
    assert registry["citation_verify"].capability is None


def test_rag_enabled_registers_rag_retrieval_and_returns_real_chunks(tmp_path):
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    (corpus_dir / "doc1.txt").write_text("Wind turbines require regular maintenance inspections.", encoding="utf-8")
    (corpus_dir / "doc2.txt").write_text("Blockchain provenance tracks data lineage across stores.", encoding="utf-8")

    agent = _make_agent(
        tmp_path,
        rag=RagSpec(enabled=True, corpus_path=str(corpus_dir)),
        permissions=PermissionsSpec(data_scopes=[str(corpus_dir)]),
    )
    registry = build_registry(agent)
    assert "rag_retrieval" in registry
    assert registry["rag_retrieval"].capability == "rag_retrieval"

    result = registry["rag_retrieval"].execute(query="turbine maintenance")
    assert "chunks" in result
    assert len(result["chunks"]) >= 1
    assert any("turbine" in c["text"].lower() for c in result["chunks"])

    # The call is logged to the trail exactly like agent.py's own
    # _rag_chunks would log it.
    conv_path = agent.storage.agent_dir(agent.card.agent_id) / "conversation.jsonl"
    logged = conv_path.read_text(encoding="utf-8")
    assert '"tool": "rag_retrieval"' in logged


def test_web_search_tool_only_registered_when_granted_via_card_tools(tmp_path):
    agent = _make_agent(tmp_path, tools=["web_search"])
    registry = build_registry(agent)
    assert "web_search" in registry
    assert registry["web_search"].capability == "web_search"


def test_web_search_execute_degrades_gracefully_on_failure(tmp_path, monkeypatch):
    import symphysis.tools.registry as registry_module

    def _boom(query, top_k=5):
        raise WebSearchError("SearXNG unreachable")

    monkeypatch.setattr(registry_module, "search_as_dicts", _boom)

    agent = _make_agent(tmp_path, tools=["web_search"])
    registry = build_registry(agent)
    result = registry["web_search"].execute(query="wind energy Spain")
    assert result["results"] == []
    assert "SearXNG unreachable" in result["error"]


def test_citation_verify_wraps_qa_checks(tmp_path):
    agent = _make_agent(tmp_path)
    registry = build_registry(agent)
    result = registry["citation_verify"].execute(claimed=["source_a", "source_z"], available_tags=["source_a"])
    assert result["genuine"] is False
    assert result["fabricated"] == ["source_z"]
