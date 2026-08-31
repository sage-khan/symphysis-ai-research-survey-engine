"""Tests for tools/authorization.py: the capability check every tool call
(via tools/proxy.py) must pass before its registry.py execute() function
ever runs. Reads real spawn_declaration.json files written by
spawning/spawn.py, not a mock."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest

from symphysis.agent_card import ModelSpec, new_card
from symphysis.audit.logger import SurveyStorage
from symphysis.policy.capability import RAG_RETRIEVAL, WEB_SEARCH
from symphysis.spawning import spawn
from symphysis.tools.authorization import ToolAuthorizationError, check_capability


def _card(tmp_path: Path, agent_id: str = "auth-test-agent", **kwargs):
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("Role: {role}\n{role_description}\n", encoding="utf-8")
    return new_card(
        agent_id=agent_id,
        role="Data Engineer",
        role_description="A test persona.",
        system_prompt_template=str(prompt),
        model=ModelSpec(provider="ollama", name="test-model"),
        did_seed="test-seed",
        **kwargs,
    )


def test_none_capability_always_passes(tmp_path):
    storage = SurveyStorage(tmp_path / "survey")
    # No spawn_declaration.json written at all, and it still passes: a
    # capability=None tool (e.g. citation_verify) needs no authorization.
    check_capability(storage, "nonexistent-agent", None)


def test_missing_declaration_raises_for_a_real_capability(tmp_path):
    storage = SurveyStorage(tmp_path / "survey")
    with pytest.raises(ToolAuthorizationError, match="no spawn_declaration.json"):
        check_capability(storage, "nonexistent-agent", RAG_RETRIEVAL)


def test_granted_capability_passes(tmp_path):
    card = _card(tmp_path, tools=["web_search"])
    storage = SurveyStorage(tmp_path / "survey")
    spawn.declare_root(storage, card, survey_id="test-survey")

    check_capability(storage, card.agent_id, WEB_SEARCH)  # must not raise


def test_ungranted_capability_raises(tmp_path):
    card = _card(tmp_path)  # no tools=[], no rag enabled: only knowledge_repo is requested/granted
    storage = SurveyStorage(tmp_path / "survey")
    spawn.declare_root(storage, card, survey_id="test-survey")

    with pytest.raises(ToolAuthorizationError, match="was not granted capability 'rag_retrieval'"):
        check_capability(storage, card.agent_id, RAG_RETRIEVAL)
