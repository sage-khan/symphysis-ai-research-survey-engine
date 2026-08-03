"""A survey's shared knowledge repository: upload once, every agent in
that survey picks it up automatically (see agentic_survey.agent's
`_knowledge_repo_chunks`, no per-agent flag needed). Distinct from a
per-role RAG corpus (`surveys/<id>/rag_corpora/<role>/`, one agent), this
is `surveys/<id>/knowledge_repo/` (whole survey).

Text extraction on upload: .md/.txt are stored as-is (the retriever already
reads those); .pdf/.docx are converted to .md text at upload time (best
effort) since the retriever only scans .txt/.md, matching this repo's
`file-read-write.md` rule that non-text formats must be converted to a
plain-text derivative before use, not parsed directly downstream.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, File, HTTPException, UploadFile

from .surveys import _existing_survey_dir

router = APIRouter(prefix="/api/surveys/{survey_id}/knowledge", tags=["knowledge"])

_ALLOWED_SUFFIXES = {".md", ".markdown", ".txt", ".pdf", ".docx"}


def _knowledge_dir(survey_id: str) -> Path:
    d = _existing_survey_dir(survey_id)
    knowledge_dir = d / "knowledge_repo"
    knowledge_dir.mkdir(parents=True, exist_ok=True)
    return knowledge_dir


def _safe_filename(name: str) -> str:
    cleaned = Path(name).name  # strip any directory components -- no path traversal
    if not cleaned or cleaned in (".", ".."):
        raise HTTPException(400, f"Invalid filename: {name!r}")
    suffix = Path(cleaned).suffix.lower()
    if suffix not in _ALLOWED_SUFFIXES:
        raise HTTPException(400, f"Unsupported file type {suffix!r}. Use .md, .txt, .pdf, or .docx.")
    return cleaned


@router.get("")
def list_knowledge_files(survey_id: str) -> List[Dict[str, Any]]:
    d = _knowledge_dir(survey_id)
    return [
        {"filename": p.name, "size_bytes": p.stat().st_size}
        for p in sorted(d.iterdir())
        if p.is_file()
    ]


@router.post("")
async def upload_knowledge_file(survey_id: str, file: UploadFile = File(...)) -> Dict[str, Any]:
    d = _knowledge_dir(survey_id)
    filename = _safe_filename(file.filename or "")
    data = await file.read()
    suffix = Path(filename).suffix.lower()

    if suffix in (".md", ".markdown", ".txt"):
        dest = d / filename
        dest.write_bytes(data)
    else:
        # .pdf / .docx: convert to a plain-text/.md derivative, per this
        # repo's file-read-write.md rule ("never parse a non-text format
        # directly downstream, convert it to .txt/.md first"). Uses the
        # same full-text extraction the survey-criteria PDF/DOCX parser
        # uses internally (not that parser's public parse_pdf/parse_docx,
        # which discards everything except lines matching its narrow
        # "CODE: Label" candidate heuristic -- a knowledge document needs
        # the actual prose, not just the handful of lines that happen to
        # look like a criterion definition).
        from .parsing.document_parser import _extract_text_docx, _extract_text_pdf

        try:
            text = _extract_text_pdf(data) if suffix == ".pdf" else _extract_text_docx(data)
        except Exception as exc:
            raise HTTPException(422, f"Could not extract text from {filename}: {exc}") from exc
        if not text or not text.strip():
            raise HTTPException(422, f"No extractable text found in {filename}.")
        dest = d / f"{Path(filename).stem}.md"
        dest.write_text(text, encoding="utf-8")

    return {"filename": dest.name, "size_bytes": dest.stat().st_size}


@router.delete("/{filename}")
def delete_knowledge_file(survey_id: str, filename: str) -> Dict[str, str]:
    d = _knowledge_dir(survey_id)
    path = d / _safe_filename(filename)
    if not path.exists():
        raise HTTPException(404, f"No knowledge file '{filename}' in survey '{survey_id}'")
    path.unlink()
    return {"status": "deleted"}
