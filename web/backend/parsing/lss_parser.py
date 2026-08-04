"""Best-effort LimeSurvey .lss (XML export) parser.

.lss files enumerate every question as a <questions><rows><row> entry with
a `title` (the question code) and a `question` (the label, often containing
HTML). This parser surfaces every question row it finds as a *candidate*
dimension; it does not try to guess which subset is the actual Best-Worst
Method L1 criteria set, since that structure varies across LimeSurvey
versions and survey designs. The human curates the candidate list in the
UI before a survey is created from it: raw exported data to canonicalise,
not something to silently reinterpret.
"""

from __future__ import annotations

import re
from typing import List

from lxml import etree

from .markdown_parser import ParsedCandidate, ParsedSurvey

_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(text: str) -> str:
    return _TAG_RE.sub("", text or "").strip()


def parse_lss(xml_bytes: bytes) -> ParsedSurvey:
    warnings: List[str] = []
    try:
        root = etree.fromstring(xml_bytes)
    except etree.XMLSyntaxError as exc:
        return ParsedSurvey(id=None, title=None, instrument=None, candidates=[], warnings=[f"Could not parse XML: {exc}"])

    title = None
    title_el = root.find(".//surveys/rows/row/surveyls_title")
    if title_el is not None and title_el.text:
        title = title_el.text.strip()

    candidates: List[ParsedCandidate] = []
    seen_codes = set()
    for row in root.findall(".//questions/rows/row"):
        code_el = row.find("title")
        label_el = row.find("question")
        if code_el is None or not (code_el.text or "").strip():
            continue
        code = code_el.text.strip()
        label = _strip_html(label_el.text) if label_el is not None else code
        if code in seen_codes:
            continue
        seen_codes.add(code)
        candidates.append(ParsedCandidate(code=code, label=label or code))

    if not candidates:
        warnings.append(
            "No <questions><rows><row> entries found. This may not be a standard .lss export, "
            "or its schema version differs from what this parser expects; review the file manually."
        )

    return ParsedSurvey(id=None, title=title, instrument=None, candidates=candidates, warnings=warnings)
