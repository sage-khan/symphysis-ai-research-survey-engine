"""Parse a structured Markdown survey definition into candidate dimensions.

Expected shape (front matter optional but recommended):

    ---
    id: my-survey
    title: My Survey Title
    instrument: bwm
    ---

    # Criteria

    - Q: Quality -- data completeness, accuracy, and timeliness
    - PT: Provenance Trust -- chain-of-custody and source credibility

Each bullet under any heading is read as `- CODE: Label` (description after
a dash/em-dash is folded into the label). This is the well-supported,
exactly-specified format; LimeSurvey .lss and PDF/DOCX are best-effort.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import yaml

_BULLET_RE = re.compile(r"^\s*[-*]\s*([A-Za-z0-9_]{1,12})\s*:\s*(.+?)\s*$")
_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


@dataclass
class ParsedCandidate:
    code: str
    label: str


@dataclass
class ParsedSurvey:
    id: Optional[str]
    title: Optional[str]
    instrument: Optional[str]
    candidates: List[ParsedCandidate] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def parse_markdown(text: str) -> ParsedSurvey:
    front: Dict[str, Any] = {}
    match = _FRONTMATTER_RE.match(text)
    body = text
    if match:
        try:
            front = yaml.safe_load(match.group(1)) or {}
        except yaml.YAMLError:
            pass
        body = text[match.end():]

    candidates: List[ParsedCandidate] = []
    seen_codes = set()
    warnings: List[str] = []
    for line in body.splitlines():
        m = _BULLET_RE.match(line)
        if not m:
            continue
        code, label = m.group(1), m.group(2)
        # Split "Label -- description" style, keep the whole thing as label
        # text since the UI lets the user trim it; just normalise dashes.
        label = re.sub(r"\s+--\s+", " -- ", label)
        if code in seen_codes:
            warnings.append(f"Duplicate code '{code}' found; kept the first occurrence.")
            continue
        seen_codes.add(code)
        candidates.append(ParsedCandidate(code=code, label=label))

    if not candidates:
        warnings.append("No '- CODE: Label' bullets found; check the document follows the expected format.")

    return ParsedSurvey(
        id=front.get("id"),
        title=front.get("title"),
        instrument=front.get("instrument"),
        candidates=candidates,
        warnings=warnings,
    )
