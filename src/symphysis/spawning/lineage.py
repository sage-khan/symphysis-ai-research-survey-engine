"""Per-survey spawn lineage: which agent spawned which, and with what
authority.

`spawn.py` calls `append` on every declared spawn (root or child), so
`lineage.json` accumulates the full parent-to-child tree for a survey run.
A root spawn (`parent_did=None`) is its own tree, one per agent in today's
flat panel; a child spawn adds an edge from its parent's DID. This is what
lets a reviewer reconstruct not just one agent's own reasoning trace but
who spawned whom and under what capabilities, across an entire run, per
`docs/architecture/governance-layer-and-runtime-backends-plan.md` §5.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from ..audit.logger import SurveyStorage

LINEAGE_FILENAME = "lineage.json"


def _path(storage: "SurveyStorage"):
    return storage.root / LINEAGE_FILENAME


def _read(storage: "SurveyStorage") -> List[Dict[str, Any]]:
    p = _path(storage)
    if not p.exists():
        return []
    return json.loads(p.read_text(encoding="utf-8"))


def append(storage: "SurveyStorage", *, child_did: str, child_agent_id: str, parent_did: Optional[str]) -> None:
    edges = _read(storage)
    edges.append(
        {
            "child_did": child_did,
            "child_agent_id": child_agent_id,
            "parent_did": parent_did,
            "declared_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    _path(storage).write_text(json.dumps(edges, indent=2), encoding="utf-8")


def tree(storage: "SurveyStorage") -> Dict[str, List[Dict[str, Any]]]:
    """Groups the flat edge list by parent_did (using the string "root" for
    None, since JSON object keys cannot be null) for a UI or report to
    render directly as a tree without re-deriving the grouping itself."""
    edges = _read(storage)
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for edge in edges:
        key = edge["parent_did"] or "root"
        grouped.setdefault(key, []).append(edge)
    return grouped
