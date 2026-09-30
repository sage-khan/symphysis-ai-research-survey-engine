"""The one authorization decision point.

Every yes/no capability check in this codebase is meant to route through
this module rather than re-implementing its own logic. Today this is a
direct glob/allowlist evaluator (the same behavior `permissions.py` already
had); it is deliberately kept small and swappable so a future
Cedar/OPA-style general policy evaluator (already named as deferred work in
this project's own README) can replace the body of `covered`/`allowed`
without changing any caller.

`policy/capability.py`'s `attenuate` (child-spawn capability intersection)
also lives behind this same "one decision point" principle, added in the
spawn-declaration phase of `docs/architecture/governance-layer-and-runtime-backends-plan.md`,
not yet present in this phase.
"""

from __future__ import annotations

from fnmatch import fnmatch
from pathlib import Path
from typing import Any, Dict, List


def covered(normalized_path: str, scope: str) -> bool:
    if fnmatch(normalized_path, scope):
        return True
    # A "<dir>/**" scope is meant to grant everything under <dir>, but is
    # also the scope a RAG-enabled agent's card.rag.corpus_path is checked
    # against directly (the corpus *root*, not a file inside it) before any
    # individual file is read. fnmatch alone requires a literal "/" after
    # "<dir>" to match "/**", which the bare root path doesn't have, so a
    # scope written exactly like its own corpus_path (the pattern this
    # app's README and every shipped example card use) would otherwise
    # reject that corpus's own root. Treat "<dir>" as covered by "<dir>/**"
    # too.
    if scope.endswith("/**") and normalized_path == scope[: -len("/**")]:
        return True
    return False


def normalize_path(path: str) -> str:
    return str(Path(path).as_posix())


def allowed(value: str, allowlist: list[str]) -> bool:
    return value in allowlist


def escalated_level_ids(levels: List[Dict[str, Any]], threshold: int) -> List[str]:
    """Which level ids in `levels` have MORE criteria (dimensions) than
    `threshold` — Phase 4's model-tiering escalation rule
    (docs/architecture/governance-layer-and-runtime-backends-plan.md):
    "a level with more than N criteria escalates to a configured
    cloud-tier model." Pure and instrument-agnostic: takes already-loaded
    level definitions (HierarchicalBWMInstrument.levels_for_panel()'s
    shape — a list of {"id": ..., "dimensions": [...], ...} dicts), not an
    instrument instance, so it has no import-time dependency on any one
    instrument module."""
    return [lvl["id"] for lvl in levels if len(lvl.get("dimensions", [])) > threshold]


def should_escalate(levels: List[Dict[str, Any]], threshold: int) -> bool:
    return bool(escalated_level_ids(levels, threshold))
