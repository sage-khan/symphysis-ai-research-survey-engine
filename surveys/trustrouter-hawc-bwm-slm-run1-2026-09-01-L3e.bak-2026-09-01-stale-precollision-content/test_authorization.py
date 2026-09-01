import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from symphysis.agent_card import PermissionsSpec
from symphysis.policy.authorization import PermissionError_, check_data_scope, check_provider_allowed


def test_check_data_scope_allows_matching_glob():
    perms = PermissionsSpec(data_scopes=["surveys/trustrouter-hawc-bwm/rag_corpora/bim-coordinator/**"])
    check_data_scope("surveys/trustrouter-hawc-bwm/rag_corpora/bim-coordinator/SOURCES.md", perms)


def test_check_data_scope_allows_the_corpus_root_itself():
    # Agent.__init__ checks card.rag.corpus_path directly (the corpus root,
    # e.g. "surveys/x/rag_corpora/bim-coordinator") before ever reading a
    # file inside it. Every shipped example card (and the README's own
    # sample Agent Card) grants that same root via a "<root>/**" scope, so
    # the root itself must be considered covered, not just paths under it.
    # Regression test for a real bug: every RAG-enabled agent card built
    # this way was silently rejected by check_data_scope and skipped by the
    # orchestrator, found via a live end-to-end run on 2026-08-03.
    perms = PermissionsSpec(data_scopes=["surveys/trustrouter-hawc-bwm/rag_corpora/bim-coordinator/**"])
    check_data_scope("surveys/trustrouter-hawc-bwm/rag_corpora/bim-coordinator", perms)


def test_check_data_scope_rejects_path_outside_scope():
    perms = PermissionsSpec(data_scopes=["surveys/trustrouter-hawc-bwm/rag_corpora/bim-coordinator/**"])
    with pytest.raises(PermissionError_):
        check_data_scope("surveys/trustrouter-hawc-bwm/rag_corpora/structural-engineer/SOURCES.md", perms)


def test_check_data_scope_rejects_a_different_roots_bare_path():
    perms = PermissionsSpec(data_scopes=["surveys/trustrouter-hawc-bwm/rag_corpora/bim-coordinator/**"])
    with pytest.raises(PermissionError_):
        check_data_scope("surveys/trustrouter-hawc-bwm/rag_corpora/structural-engineer", perms)


def test_check_data_scope_rejects_when_no_scopes_granted():
    perms = PermissionsSpec(data_scopes=[])
    with pytest.raises(PermissionError_):
        check_data_scope("anything", perms)


def test_check_provider_allowed_passes_for_listed_provider():
    perms = PermissionsSpec(allowed_providers=["ollama", "manual"])
    check_provider_allowed("ollama", perms)


def test_check_provider_allowed_rejects_unlisted_provider():
    perms = PermissionsSpec(allowed_providers=["ollama"])
    with pytest.raises(PermissionError_):
        check_provider_allowed("openai", perms)
