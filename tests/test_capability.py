import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from symphysis.agent_card import ModelSpec, RagSpec, new_card
from symphysis.policy.capability import (
    KNOWLEDGE_REPO,
    RAG_RETRIEVAL,
    WEB_SEARCH,
    attenuate,
    capabilities_from_card,
)


def _card(tmp_path: Path, **kwargs):
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("Role: {role}\n{role_description}\n", encoding="utf-8")
    return new_card(
        agent_id="cap-test-agent",
        role="Data Engineer",
        role_description="A test persona.",
        system_prompt_template=str(prompt),
        model=ModelSpec(provider="ollama", name="test-model"),
        did_seed="test-seed",
        **kwargs,
    )


def test_capabilities_from_card_always_includes_knowledge_repo(tmp_path):
    card = _card(tmp_path)
    assert KNOWLEDGE_REPO in capabilities_from_card(card)


def test_capabilities_from_card_includes_rag_only_when_enabled(tmp_path):
    without_rag = _card(tmp_path)
    assert RAG_RETRIEVAL not in capabilities_from_card(without_rag)

    with_rag = _card(tmp_path, rag=RagSpec(enabled=True, corpus_path="surveys/x/rag_corpora/y"))
    assert RAG_RETRIEVAL in capabilities_from_card(with_rag)


def test_capabilities_from_card_includes_web_search_only_when_in_tools(tmp_path):
    without_search = _card(tmp_path)
    assert WEB_SEARCH not in capabilities_from_card(without_search)

    with_search = _card(tmp_path, tools=["web_search"])
    assert WEB_SEARCH in capabilities_from_card(with_search)


def test_attenuate_is_intersection_not_union():
    parent_granted = [RAG_RETRIEVAL, KNOWLEDGE_REPO]
    requested = [RAG_RETRIEVAL, WEB_SEARCH]
    assert attenuate(parent_granted, requested) == [RAG_RETRIEVAL]


def test_attenuate_never_grants_more_than_parent_holds():
    # A child requesting everything, from a parent holding nothing, gets nothing.
    assert attenuate([], [RAG_RETRIEVAL, WEB_SEARCH, KNOWLEDGE_REPO]) == []


def test_attenuate_preserves_requested_order():
    parent_granted = [WEB_SEARCH, RAG_RETRIEVAL, KNOWLEDGE_REPO]
    requested = [KNOWLEDGE_REPO, RAG_RETRIEVAL]
    assert attenuate(parent_granted, requested) == [KNOWLEDGE_REPO, RAG_RETRIEVAL]
