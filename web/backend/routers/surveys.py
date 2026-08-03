"""Survey CRUD, document parsing, run, results, and download endpoints."""

from __future__ import annotations

import io
import json
import re
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from .. import runs
from ..analytics import compute_analytics
from ..paths import CONFIG_DIR, SURVEYS_ROOT, survey_dir
from ..parsing.document_parser import parse_docx, parse_pdf
from ..parsing.lss_parser import parse_lss
from ..parsing.markdown_parser import parse_markdown

router = APIRouter(prefix="/api/surveys", tags=["surveys"])

_ID_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$")


def _safe_id(value: str, kind: str = "id") -> str:
    if not _ID_RE.match(value):
        raise HTTPException(400, f"Invalid {kind}: {value!r}. Use letters, digits, '-', '_' only.")
    return value


def _existing_survey_dir(survey_id: str) -> Path:
    d = survey_dir(_safe_id(survey_id, "survey_id"))
    if not (d / "survey.yaml").exists():
        raise HTTPException(404, f"No survey '{survey_id}'")
    return d


class CriterionIn(BaseModel):
    code: str
    label: str


class CreateSurveyIn(BaseModel):
    id: str
    title: str
    description: str = ""
    instrument: str = "bwm"
    criteria: List[CriterionIn]
    headline_alpha: float = 0.6
    alpha_sweep: List[float] = [0, 0.2, 0.4, 0.5, 0.6, 0.8, 1.0]


class RenameSurveyIn(BaseModel):
    title: str


class SurveyRulefileIn(BaseModel):
    content: str


@router.get("")
def list_surveys() -> List[Dict[str, Any]]:
    out = []
    for d in sorted(SURVEYS_ROOT.iterdir()):
        survey_yaml = d / "survey.yaml"
        if not survey_yaml.exists():
            continue
        data = yaml.safe_load(survey_yaml.read_text(encoding="utf-8")) or {}
        agents_dir = d / "agents"
        agent_count = len(list(agents_dir.glob("*.json"))) if agents_dir.exists() else 0
        out.append(
            {
                "id": data.get("id", d.name),
                "title": data.get("title", d.name),
                "description": data.get("description", ""),
                "instrument": data.get("instrument"),
                "agent_count": agent_count,
                "has_results": (d / "report" / "combined_results.json").exists(),
                "run_status": runs.get_status(d.name)["status"],
                "created_at": data.get("created_at"),
            }
        )
    return out


@router.get("/{survey_id}")
def get_survey(survey_id: str) -> Dict[str, Any]:
    d = _existing_survey_dir(survey_id)
    data = yaml.safe_load((d / "survey.yaml").read_text(encoding="utf-8")) or {}
    return {**data, "run_status": runs.get_status(survey_id)}


@router.post("/parse")
async def parse_document(file: UploadFile = File(...)) -> Dict[str, Any]:
    data = await file.read()
    name = (file.filename or "").lower()

    if name.endswith(".md") or name.endswith(".markdown"):
        parsed = parse_markdown(data.decode("utf-8", errors="replace"))
    elif name.endswith(".lss") or name.endswith(".xml"):
        parsed = parse_lss(data)
    elif name.endswith(".pdf"):
        parsed = parse_pdf(data)
    elif name.endswith(".docx"):
        parsed = parse_docx(data)
    else:
        raise HTTPException(400, f"Unsupported file type: {file.filename}. Use .md, .lss, .pdf, or .docx.")

    return {
        "id": parsed.id,
        "title": parsed.title,
        "instrument": parsed.instrument,
        "candidates": [{"code": c.code, "label": c.label} for c in parsed.candidates],
        "warnings": parsed.warnings,
    }


@router.post("")
def create_survey(body: CreateSurveyIn) -> Dict[str, Any]:
    survey_id = _safe_id(body.id, "id")
    d = survey_dir(survey_id)
    if (d / "survey.yaml").exists():
        raise HTTPException(409, f"Survey '{survey_id}' already exists.")
    if not body.criteria:
        raise HTTPException(400, "At least one criterion is required.")

    (d / "agents").mkdir(parents=True, exist_ok=True)
    survey_yaml = {
        "id": survey_id,
        "title": body.title,
        "description": body.description,
        "instrument": body.instrument,
        "instrument_params": {
            "dimensions": [c.code for c in body.criteria],
            "dimension_labels": {c.code: c.label for c in body.criteria},
        },
        "weighting": {
            "headline_alpha": body.headline_alpha,
            "alpha_sweep": body.alpha_sweep,
        },
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    (d / "survey.yaml").write_text(yaml.dump(survey_yaml, sort_keys=False), encoding="utf-8")
    return get_survey(survey_id)


@router.patch("/{survey_id}")
def rename_survey(survey_id: str, body: RenameSurveyIn) -> Dict[str, Any]:
    """Renames a survey's display title. The survey_id itself (the URL slug
    and directory name) is intentionally immutable: every agent card's
    permissions.data_scopes and rag.corpus_path bake in the literal
    `surveys/<id>/...` path, so renaming the id would require rewriting
    every agent card in the survey too. The title is what's shown everywhere
    in the UI; this is what "renaming a project" means in practice."""
    d = _existing_survey_dir(survey_id)
    data = yaml.safe_load((d / "survey.yaml").read_text(encoding="utf-8")) or {}
    if not body.title.strip():
        raise HTTPException(400, "Title cannot be empty.")
    data["title"] = body.title.strip()
    (d / "survey.yaml").write_text(yaml.dump(data, sort_keys=False), encoding="utf-8")
    return get_survey(survey_id)


@router.delete("/{survey_id}")
def delete_survey(survey_id: str) -> Dict[str, str]:
    d = _existing_survey_dir(survey_id)
    shutil.rmtree(d)
    return {"status": "deleted"}


@router.get("/{survey_id}/rulefile")
def get_survey_rulefile(survey_id: str) -> Dict[str, str]:
    """This survey's own rules, applied to every agent in it: between the
    global rulefile (every survey) and an individual agent's own rulefile
    (see Agent._rules_section). Empty by default, no separate file until
    something is actually saved here."""
    d = _existing_survey_dir(survey_id)
    path = d / "rulefile.md"
    return {"content": path.read_text(encoding="utf-8") if path.exists() else ""}


@router.put("/{survey_id}/rulefile")
def set_survey_rulefile(survey_id: str, body: SurveyRulefileIn) -> Dict[str, str]:
    d = _existing_survey_dir(survey_id)
    (d / "rulefile.md").write_text(body.content, encoding="utf-8")
    return {"content": body.content}


@router.post("/{survey_id}/run")
def run_survey_endpoint(survey_id: str) -> Dict[str, Any]:
    d = _existing_survey_dir(survey_id)
    agents_dir = d / "agents"
    if not list(agents_dir.glob("*.json")):
        raise HTTPException(400, "This survey has no agents yet. Add at least one before running.")
    try:
        runs.start_run(survey_id, d)
    except RuntimeError as exc:
        raise HTTPException(409, str(exc)) from exc
    return runs.get_status(survey_id)


@router.get("/{survey_id}/run-status")
def run_status(survey_id: str) -> Dict[str, Any]:
    _existing_survey_dir(survey_id)
    return runs.get_status(survey_id)


@router.get("/{survey_id}/results")
def get_results(survey_id: str) -> Dict[str, Any]:
    d = _existing_survey_dir(survey_id)
    combined_path = d / "report" / "combined_results.json"
    report_path = d / "report" / "report.md"
    if not combined_path.exists():
        raise HTTPException(404, "No results yet; run the survey first.")
    return {
        "combined_results": json.loads(combined_path.read_text(encoding="utf-8")),
        "report_markdown": report_path.read_text(encoding="utf-8") if report_path.exists() else "",
        "charts": [p.name for p in sorted((d / "report" / "charts").glob("*.png"))] if (d / "report" / "charts").exists() else [],
    }


@router.get("/{survey_id}/analytics")
def get_analytics(survey_id: str) -> Dict[str, Any]:
    """Weight-elicitation analytics: every accepted sample's Best/Worst pick
    and reasoning, grouped by agent, plus a Best/Worst frequency count per
    criterion and an honest accounting of which configured agents didn't
    contribute (and why: skipped, zero-accepted, pending manual, not run).
    Derived entirely from what's on disk; never fabricates a result for an
    agent that didn't produce one."""
    d = _existing_survey_dir(survey_id)
    return compute_analytics(d)


@router.get("/{survey_id}/charts/{chart_name}")
def get_chart(survey_id: str, chart_name: str):
    from fastapi.responses import FileResponse

    d = _existing_survey_dir(survey_id)
    if not re.match(r"^[a-zA-Z0-9_.-]+\.png$", chart_name):
        raise HTTPException(400, "Invalid chart filename.")
    path = d / "report" / "charts" / chart_name
    if not path.exists():
        raise HTTPException(404, "Chart not found.")
    return FileResponse(path, media_type="image/png")


@router.get("/{survey_id}/integrity")
def get_integrity_manifest(survey_id: str) -> Dict[str, Any]:
    """The SHA-256 manifest written right after this survey's last run (see
    orchestrator.run_survey), if one exists yet. This is the record to cite
    or archive; verify_integrity below is how to check it still matches."""
    from agentic_survey import integrity

    d = _existing_survey_dir(survey_id)
    manifest = integrity.load_manifest(d)
    if manifest is None:
        raise HTTPException(404, "No integrity manifest yet; run the survey first.")
    return manifest


@router.get("/{survey_id}/verify-integrity")
def verify_integrity(survey_id: str) -> Dict[str, Any]:
    """Recomputes every file's hash right now and compares against the
    stored manifest: an honest pass/fail, not a similarity score. Use this
    to confirm a survey folder (this copy, or one received from someone
    else) has not been altered since its manifest was generated."""
    from agentic_survey import integrity

    d = _existing_survey_dir(survey_id)
    result = integrity.verify(d)
    if result.manifest_root_hash is None:
        raise HTTPException(404, "No integrity manifest yet; run the survey first.")
    return integrity.verification_to_dict(result)


@router.get("/{survey_id}/download")
def download_survey(survey_id: str):
    d = _existing_survey_dir(survey_id)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in d.rglob("*"):
            if path.is_file():
                zf.write(path, arcname=str(path.relative_to(d.parent)))
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{survey_id}.zip"'},
    )
