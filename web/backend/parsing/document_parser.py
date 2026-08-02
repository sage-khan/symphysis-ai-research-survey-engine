"""Best-effort PDF/DOCX candidate-dimension extraction.

Extracts full text, then applies a simple heuristic (a short code-like
token followed by a separator and a label, one per line) to surface
candidates. This is explicitly rougher than the Markdown or .lss parsers:
free-form prose documents don't have a reliable structural marker for
"this is a criterion," so every candidate this heuristic finds must be
reviewed and corrected in the UI before a survey is created from it, not
trusted as-is.
"""

from __future__ import annotations

import io
import re
from typing import List

import pdfplumber
from docx import Document as DocxDocument

from .markdown_parser import ParsedCandidate, ParsedSurvey

_CANDIDATE_LINE_RE = re.compile(r"^\s*[-*\d.)]*\s*([A-Za-z]{1,8})\s*[:\-–—]\s*(.{3,120})\s*$")


def _extract_text_pdf(data: bytes) -> str:
    text_parts: List[str] = []
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for page in pdf.pages:
            text_parts.append(page.extract_text() or "")
    return "\n".join(text_parts)


def _extract_text_docx(data: bytes) -> str:
    doc = DocxDocument(io.BytesIO(data))
    return "\n".join(p.text for p in doc.paragraphs)


def _candidates_from_text(text: str) -> List[ParsedCandidate]:
    candidates: List[ParsedCandidate] = []
    seen = set()
    for line in text.splitlines():
        m = _CANDIDATE_LINE_RE.match(line)
        if not m:
            continue
        code, label = m.group(1).upper(), m.group(2).strip()
        if code in seen:
            continue
        seen.add(code)
        candidates.append(ParsedCandidate(code=code, label=label))
    return candidates


def parse_pdf(data: bytes) -> ParsedSurvey:
    text = _extract_text_pdf(data)
    candidates = _candidates_from_text(text)
    warnings = [
        "PDF extraction is best-effort text-pattern matching, not structural parsing. "
        "Review every candidate below before creating the survey; add or remove rows freely."
    ]
    if not candidates:
        warnings.append("No candidate lines matched the 'CODE: Label' heuristic pattern.")
    return ParsedSurvey(id=None, title=None, instrument=None, candidates=candidates, warnings=warnings)


def parse_docx(data: bytes) -> ParsedSurvey:
    text = _extract_text_docx(data)
    candidates = _candidates_from_text(text)
    warnings = [
        "DOCX extraction is best-effort text-pattern matching, not structural parsing. "
        "Review every candidate below before creating the survey; add or remove rows freely."
    ]
    if not candidates:
        warnings.append("No candidate lines matched the 'CODE: Label' heuristic pattern.")
    return ParsedSurvey(id=None, title=None, instrument=None, candidates=candidates, warnings=warnings)
