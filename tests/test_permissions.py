import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentic_survey.agent_card import PermissionsSpec
from agentic_survey.permissions import PermissionError_, check_data_scope, check_provider_allowed


def test_check_data_scope_allows_matching_glob():
    perms = PermissionsSpec(data_scopes=["surveys/bsi-hawc-bwm/rag_corpora/bim-coordinator/**"])
    check_data_scope("surveys/bsi-hawc-bwm/rag_corpora/bim-coordinator/SOURCES.md", perms)


def test_check_data_scope_rejects_path_outside_scope():
    perms = PermissionsSpec(data_scopes=["surveys/bsi-hawc-bwm/rag_corpora/bim-coordinator/**"])
    with pytest.raises(PermissionError_):
        check_data_scope("surveys/bsi-hawc-bwm/rag_corpora/structural-engineer/SOURCES.md", perms)


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
