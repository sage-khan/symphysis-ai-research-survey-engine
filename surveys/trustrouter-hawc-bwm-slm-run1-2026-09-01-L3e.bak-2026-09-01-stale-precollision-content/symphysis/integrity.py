"""Tamper-evidence for a completed survey's full output.

Every prompt, response, guardrail decision, and result in a survey run is
already written to plain files (see storage.py). That transparency is only
as good as the guarantee that those files are the same ones a reviewer
reads later. This module closes that gap with a standard, tool-independent
mechanism: a SHA-256 hash of every file at the moment a run completes, a
single root hash summarizing all of them, and a `SHA256SUMS` file in the
exact format `sha256sum -c` already understands, so a reviewer can verify
integrity with a coreutils command already on their machine, no copy of
this application required.

This detects alteration; it does not prevent someone with access to the
survey folder from silently overwriting both the files and the manifest
together. What it guarantees is that a manifest recorded once (kept
separately, cited in a paper, or externally timestamped) makes any *later*
change to the survey folder detectable, and that the detection method
itself needs no proprietary tooling to check.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

MANIFEST_FILENAME = "integrity_manifest.json"
SHA256SUMS_FILENAME = "SHA256SUMS"

# Never hash the integrity files themselves, or generating the manifest
# would need to already know its own hash before it exists.
_EXCLUDED = {MANIFEST_FILENAME, SHA256SUMS_FILENAME}


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _iter_files(survey_dir: Path) -> List[Path]:
    return sorted(
        p for p in survey_dir.rglob("*")
        if p.is_file() and p.name not in _EXCLUDED
    )


def compute_file_hashes(survey_dir: Path) -> Dict[str, str]:
    """Relative path (posix-style, stable across OSes) -> hex SHA-256, for
    every file currently under survey_dir, in deterministic sorted order."""
    return {
        str(p.relative_to(survey_dir).as_posix()): _sha256_file(p)
        for p in _iter_files(survey_dir)
    }


def compute_root_hash(file_hashes: Dict[str, str]) -> str:
    """A single hash summarizing every file hash: SHA-256 of the sorted
    "path\\thash" lines joined by newlines. Sorted by path so the root hash
    is identical regardless of filesystem iteration order."""
    lines = [f"{path}\t{h}" for path, h in sorted(file_hashes.items())]
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def write_manifest(survey_dir: Path) -> Dict[str, Any]:
    """Called once, right after a survey run's report is written (see
    orchestrator.run_survey). Writes both the JSON manifest and a plain
    SHA256SUMS file, and returns the manifest dict."""
    file_hashes = compute_file_hashes(survey_dir)
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "file_count": len(file_hashes),
        "files": file_hashes,
        "root_hash": compute_root_hash(file_hashes),
        "hash_algorithm": "sha256",
    }
    (survey_dir / MANIFEST_FILENAME).write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    sha256sums_lines = [f"{h}  {path}" for path, h in sorted(file_hashes.items())]
    (survey_dir / SHA256SUMS_FILENAME).write_text("\n".join(sha256sums_lines) + "\n", encoding="utf-8")
    return manifest


def load_manifest(survey_dir: Path) -> Dict[str, Any] | None:
    path = survey_dir / MANIFEST_FILENAME
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


@dataclass
class VerificationResult:
    ok: bool
    manifest_generated_at: str | None
    manifest_root_hash: str | None
    current_root_hash: str | None
    changed: List[str]
    added: List[str]
    removed: List[str]
    matched_count: int


def verify(survey_dir: Path) -> VerificationResult:
    """Recomputes every file's hash right now and compares against the
    stored manifest. `ok` is True only if nothing changed, nothing was
    added, and nothing was removed since the manifest was written: an
    honest, unqualified verification, not a partial-credit score."""
    manifest = load_manifest(survey_dir)
    if manifest is None:
        return VerificationResult(
            ok=False, manifest_generated_at=None, manifest_root_hash=None,
            current_root_hash=None, changed=[], added=[], removed=[], matched_count=0,
        )

    stored = manifest["files"]
    current = compute_file_hashes(survey_dir)

    changed = sorted(p for p in stored.keys() & current.keys() if stored[p] != current[p])
    removed = sorted(stored.keys() - current.keys())
    added = sorted(current.keys() - stored.keys())
    matched_count = len(stored) - len(changed) - len(removed)

    return VerificationResult(
        ok=not changed and not removed and not added,
        manifest_generated_at=manifest.get("generated_at"),
        manifest_root_hash=manifest.get("root_hash"),
        current_root_hash=compute_root_hash(current),
        changed=changed,
        added=added,
        removed=removed,
        matched_count=matched_count,
    )


def verification_to_dict(result: VerificationResult) -> Dict[str, Any]:
    return {
        "ok": result.ok,
        "manifest_generated_at": result.manifest_generated_at,
        "manifest_root_hash": result.manifest_root_hash,
        "current_root_hash": result.current_root_hash,
        "changed": result.changed,
        "added": result.added,
        "removed": result.removed,
        "matched_count": result.matched_count,
    }
