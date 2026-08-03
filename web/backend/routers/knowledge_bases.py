"""Reusable, named domain-knowledge bases: upload files once under
agents_library/knowledge_bases/<kb_id>/, then point any agent's
rag.corpus_path at that same directory to reuse it, instead of
re-uploading the same files into a one-off per-agent corpus every time a
new agent needs the same background material.

This is a thin wrapper around the same directory-of-.md/.txt-files
contract agentic_survey.rag.retriever already reads for any
rag.corpus_path (see instruments/base.py / agent.py): a "knowledge base"
is not a new storage concept, it is a named, listed, reusable instance of
the one that already exists, kept in agents_library/ so it is visible and
assignable from the Agent Library UI rather than only creatable by editing
a JSON file's corpus_path by hand.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from ..paths import LIBRARY_ROOT

router = APIRouter(prefix="/api/knowledge-bases", tags=["knowledge-bases"])

_ALLOWED_SUFFIXES = {".md", ".markdown", ".txt", ".pdf", ".docx"}
_KB_ROOT = LIBRARY_ROOT / "knowledge_bases"


class KnowledgeBaseIn(BaseModel):
    id: str
    name: str
    description: str = ""


def _safe_id(value: str, field: str) -> str:
    cleaned = value.strip()
    if not cleaned or cleaned != Path(cleaned).name or cleaned in (".", ".."):
        raise HTTPException(400, f"Invalid {field}: {value!r}")
    return cleaned


def _safe_filename(name: str) -> str:
    cleaned = Path(name).name
    if not cleaned or cleaned in (".", ".."):
        raise HTTPException(400, f"Invalid filename: {name!r}")
    suffix = Path(cleaned).suffix.lower()
    if suffix not in _ALLOWED_SUFFIXES:
        raise HTTPException(400, f"Unsupported file type {suffix!r}. Use .md, .txt, .pdf, or .docx.")
    return cleaned


def _kb_dir(kb_id: str) -> Path:
    return _KB_ROOT / _safe_id(kb_id, "kb_id")


def _metadata_path(kb_id: str) -> Path:
    return _kb_dir(kb_id) / "metadata.json"


def _read_metadata(kb_id: str) -> Dict[str, Any]:
    path = _metadata_path(kb_id)
    if not path.exists():
        raise HTTPException(404, f"No knowledge base '{kb_id}'")
    return json.loads(path.read_text(encoding="utf-8"))


def _corpus_path_for(kb_id: str) -> str:
    """The path an Agent Card's rag.corpus_path should be set to, to reuse
    this knowledge base: relative to repo root, matching how every other
    corpus_path in this app is written."""
    return f"agents_library/knowledge_bases/{kb_id}"


def _list_files(kb_id: str) -> List[Dict[str, Any]]:
    d = _kb_dir(kb_id)
    return [
        {"filename": p.name, "size_bytes": p.stat().st_size}
        for p in sorted(d.iterdir())
        if p.is_file() and p.name != "metadata.json"
    ]


def _summary(kb_id: str) -> Dict[str, Any]:
    meta = _read_metadata(kb_id)
    files = _list_files(kb_id)
    return {
        "id": kb_id,
        "name": meta.get("name", kb_id),
        "description": meta.get("description", ""),
        "created_at": meta.get("created_at"),
        "corpus_path": _corpus_path_for(kb_id),
        "files": files,
        "file_count": len(files),
    }


@router.get("")
def list_knowledge_bases() -> List[Dict[str, Any]]:
    if not _KB_ROOT.exists():
        return []
    return [_summary(p.name) for p in sorted(_KB_ROOT.iterdir()) if p.is_dir()]


@router.post("")
def create_knowledge_base(body: KnowledgeBaseIn) -> Dict[str, Any]:
    kb_id = _safe_id(body.id, "id")
    d = _kb_dir(kb_id)
    if d.exists():
        raise HTTPException(409, f"Knowledge base '{kb_id}' already exists.")
    d.mkdir(parents=True)
    metadata = {
        "id": kb_id,
        "name": body.name,
        "description": body.description,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _metadata_path(kb_id).write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return _summary(kb_id)


@router.delete("/{kb_id}")
def delete_knowledge_base(kb_id: str) -> Dict[str, str]:
    d = _kb_dir(kb_id)
    if not d.exists():
        raise HTTPException(404, f"No knowledge base '{kb_id}'")
    for p in d.iterdir():
        p.unlink()
    d.rmdir()
    return {"status": "deleted"}


@router.post("/{kb_id}/files")
async def upload_knowledge_base_file(kb_id: str, file: UploadFile = File(...)) -> Dict[str, Any]:
    d = _kb_dir(kb_id)
    if not d.exists():
        raise HTTPException(404, f"No knowledge base '{kb_id}'")
    filename = _safe_filename(file.filename or "")
    data = await file.read()
    suffix = Path(filename).suffix.lower()

    if suffix in (".md", ".markdown", ".txt"):
        dest = d / filename
        dest.write_bytes(data)
    else:
        # .pdf / .docx: convert to a plain-text/.md derivative first, per
        # this repo's file-read-write.md rule; matches knowledge.py's
        # survey-level knowledge_repo upload handling exactly.
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


@router.delete("/{kb_id}/files/{filename}")
def delete_knowledge_base_file(kb_id: str, filename: str) -> Dict[str, str]:
    d = _kb_dir(kb_id)
    if not d.exists():
        raise HTTPException(404, f"No knowledge base '{kb_id}'")
    path = d / _safe_filename(filename)
    if not path.exists():
        raise HTTPException(404, f"No file '{filename}' in knowledge base '{kb_id}'")
    path.unlink()
    return {"status": "deleted"}
