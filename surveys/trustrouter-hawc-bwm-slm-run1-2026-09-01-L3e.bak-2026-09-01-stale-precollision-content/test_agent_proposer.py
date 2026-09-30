import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "web"))

from backend.agent_proposer import ProposalError, parse_proposals


def test_parses_a_mix_of_library_and_new_entries():
    raw = """Here is my proposal:
    [
      {"source": "library", "agent_id": "existing-agent"},
      {"source": "new", "agent_id": "new-agent", "display_name": "Dr. X", "role": "Tester", "role_description": "A test persona.", "model": {"provider": "ollama", "name": "qwen2.5:14b"}}
    ]
    Let me know if you'd like changes.
    """
    result = parse_proposals(raw, known_library_ids=["existing-agent"])
    assert len(result) == 2
    assert result[0]["source"] == "library"
    assert result[1]["agent_id"] == "new-agent"


def test_rejects_no_json_array():
    with pytest.raises(ProposalError):
        parse_proposals("Sorry, I can't help with that.", known_library_ids=[])


def test_rejects_malformed_json():
    with pytest.raises(ProposalError):
        parse_proposals("[{\"source\": \"new\", oops}]", known_library_ids=[])


def test_rejects_library_entry_referencing_unknown_id():
    raw = '[{"source": "library", "agent_id": "does-not-exist"}]'
    with pytest.raises(ProposalError, match="does-not-exist"):
        parse_proposals(raw, known_library_ids=["some-other-agent"])


def test_rejects_new_entry_missing_required_field():
    raw = '[{"source": "new", "agent_id": "x", "role": "Tester"}]'
    with pytest.raises(ProposalError, match="role_description"):
        parse_proposals(raw, known_library_ids=[])


def test_rejects_duplicate_new_agent_ids():
    raw = """[
      {"source": "new", "agent_id": "dup", "role": "A", "role_description": "d", "model": {"provider": "ollama", "name": "m"}},
      {"source": "new", "agent_id": "dup", "role": "B", "role_description": "d", "model": {"provider": "ollama", "name": "m"}}
    ]"""
    with pytest.raises(ProposalError, match="unique"):
        parse_proposals(raw, known_library_ids=[])


def test_rejects_new_agent_id_colliding_with_library():
    raw = '[{"source": "new", "agent_id": "existing-agent", "role": "A", "role_description": "d", "model": {"provider": "ollama", "name": "m"}}]'
    with pytest.raises(ProposalError, match="unique"):
        parse_proposals(raw, known_library_ids=["existing-agent"])


def test_rejects_invalid_source_value():
    raw = '[{"source": "made-up", "agent_id": "x"}]'
    with pytest.raises(ProposalError, match="library.*or.*new"):
        parse_proposals(raw, known_library_ids=[])


def test_flags_hallucinated_model_not_actually_available(monkeypatch):
    from backend import agent_proposer, model_catalog

    monkeypatch.setattr(model_catalog, "list_models", lambda p: {"models": ["qwen2.5:14b", "mistral:7b"], "error": None})
    proposals = [
        {"source": "new", "agent_id": "a", "model": {"provider": "ollama", "name": "qwen2.5:14b"}},
        {"source": "new", "agent_id": "b", "model": {"provider": "ollama", "name": "code-davinci"}},
        {"source": "library", "agent_id": "c"},
    ]
    agent_proposer._annotate_model_availability(proposals)
    assert proposals[0]["model_available"] is True
    assert proposals[1]["model_available"] is False
    assert "model_available" not in proposals[2]


def test_skips_availability_check_for_manual_provider(monkeypatch):
    from backend import agent_proposer, model_catalog

    calls = []
    monkeypatch.setattr(model_catalog, "list_models", lambda p: calls.append(p) or {"models": [], "error": "no list"})
    proposals = [{"source": "new", "agent_id": "a", "model": {"provider": "manual", "name": "gemini-2.5-pro"}}]
    agent_proposer._annotate_model_availability(proposals)
    assert "model_available" not in proposals[0]
    assert calls == []  # never even asked: manual has no API list by definition


def test_gives_benefit_of_the_doubt_when_catalog_unreachable(monkeypatch):
    from backend import agent_proposer, model_catalog

    monkeypatch.setattr(model_catalog, "list_models", lambda p: {"models": [], "error": "unreachable"})
    proposals = [{"source": "new", "agent_id": "a", "model": {"provider": "ollama", "name": "anything"}}]
    agent_proposer._annotate_model_availability(proposals)
    assert proposals[0]["model_available"] is True
