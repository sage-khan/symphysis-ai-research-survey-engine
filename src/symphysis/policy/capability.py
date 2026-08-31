"""The capability vocabulary + attenuation rule.

A capability is a short, stable string naming one thing an agent may do.
This list starts minimal, matching only what today's codebase actually
gates (`agent.py`'s `_rag_chunks`/`_web_search_chunks`/`_knowledge_repo_chunks`
methods): extend it only when a real caller needs a new one, per
`docs/architecture/governance-layer-and-runtime-backends-plan.md` §2's
"no capability nothing uses yet" principle.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List

RAG_RETRIEVAL = "rag_retrieval"
WEB_SEARCH = "web_search"
KNOWLEDGE_REPO = "knowledge_repo"
CODE_EXECUTION = "code_execution"  # reserved: gates OpenManus's python_execute/bash tools, granted to no role today
FILESYSTEM_WRITE = "filesystem_write"  # reserved: gates OpenManus's str_replace_editor tool, granted to no role today
SPAWN_CHILD = "spawn_child"  # reserved: whether an agent may itself spawn a child agent

ALL_CAPABILITIES = frozenset(
    {RAG_RETRIEVAL, WEB_SEARCH, KNOWLEDGE_REPO, CODE_EXECUTION, FILESYSTEM_WRITE, SPAWN_CHILD}
)

if TYPE_CHECKING:
    from ..agent_card import AgentCard


def capabilities_from_card(card: "AgentCard") -> List[str]:
    """Derive a root agent's requested capabilities from its existing
    AgentCard fields, so today's cards (authored before this capability
    vocabulary existed) get a correct declaration with no card migration
    required. KNOWLEDGE_REPO is always requested: `agent.py`'s
    `_knowledge_repo_chunks` auto-detects a survey-level shared corpus with
    no per-agent opt-in flag, so "may use it if present" is the accurate
    capability, not a per-card setting."""
    caps = [KNOWLEDGE_REPO]
    if card.rag.enabled:
        caps.append(RAG_RETRIEVAL)
    if "web_search" in card.tools:
        caps.append(WEB_SEARCH)
    return caps


def attenuate(parent_granted: List[str], requested: List[str]) -> List[str]:
    """The one attenuation rule in this codebase: a child's granted
    capabilities are the intersection of what its parent itself holds and
    what it asked for, NEVER a union. A parent can only delegate authority
    it actually has. Order follows `requested`, so a caller inspecting the
    result sees capabilities in the order the child asked for them."""
    parent_set = set(parent_granted)
    return [c for c in requested if c in parent_set]
