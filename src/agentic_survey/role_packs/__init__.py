"""Standard role knowledge packs: short, curated professional-domain
primers that get attached as extra context to an agent whose role_pack
matches one of these files, so a freshly created "Data Engineer" agent
can speak from that professional standpoint immediately rather than
from a blank role_description alone.

Each pack is a single markdown file in role_packs/, shaped as:

    # <Title>
    Summary: <one-line description shown in the picker>

    <body -- the actual reference content included as agent context>

This is genuine, well-established professional-domain knowledge (named
standards, common failure modes, evaluation heuristics) -- not
survey-specific facts, and not a substitute for an agent's own dedicated
RAG corpus or the survey's shared knowledge repo. It plays the same role
a textbook chapter or onboarding primer would play for a new human
panelist stepping into that professional role.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

ROLE_PACKS_DIR = Path(__file__).parent / "packs"


@dataclass
class RolePackInfo:
    id: str
    label: str
    summary: str


def _summary_line_index(lines: List[str]) -> Optional[int]:
    for i, line in enumerate(lines[:4]):
        if line.startswith("Summary:"):
            return i
    return None


def _parse(path: Path) -> RolePackInfo:
    lines = path.read_text(encoding="utf-8").splitlines()
    title = lines[0].lstrip("#").strip() if lines else path.stem
    idx = _summary_line_index(lines)
    summary = lines[idx][len("Summary:"):].strip() if idx is not None else ""
    return RolePackInfo(id=path.stem, label=title, summary=summary)


def list_role_packs() -> List[Dict[str, str]]:
    """Every available pack, discovered from the filesystem -- never a
    hardcoded list, so adding a new .md file to role_packs/ is enough to
    expose a new pack in the UI picker without a code change."""
    if not ROLE_PACKS_DIR.is_dir():
        return []
    packs = [_parse(p) for p in sorted(ROLE_PACKS_DIR.glob("*.md"))]
    return [{"id": p.id, "label": p.label, "summary": p.summary} for p in packs]


def get_role_pack_text(pack_id: Optional[str]) -> Optional[str]:
    """The pack's body content (title/summary header stripped), or None if
    pack_id is unset or no longer matches any known pack -- an agent whose
    role_pack was hand-typed or whose pack file was removed degrades to no
    extra context, exactly like an agent with no role_pack set at all."""
    if not pack_id:
        return None
    path = ROLE_PACKS_DIR / f"{pack_id}.md"
    if not path.exists():
        return None
    lines = path.read_text(encoding="utf-8").splitlines()
    idx = _summary_line_index(lines)
    body_start = (idx + 1) if idx is not None else 0
    while body_start < len(lines) and not lines[body_start].strip():
        body_start += 1
    return "\n".join(lines[body_start:]).strip()
