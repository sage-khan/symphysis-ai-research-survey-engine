"""Shared path resolution: where this app's source lives and where survey
projects are stored, both relative to the repo root regardless of the
process's current working directory."""

from __future__ import annotations

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = REPO_ROOT / "src"
SURVEYS_ROOT = Path(os.environ.get("SURVEYS_ROOT", REPO_ROOT / "surveys"))
CONFIG_DIR = REPO_ROOT / "config"
# Reusable Agent Cards not tied to any one survey (see routers/library.py).
# "Assigning" one to a survey copies its card into that survey's own
# agents/ directory -- the orchestrator/storage/run pipeline only ever
# reads surveys/<id>/agents/*.json, so this keeps that pipeline unchanged.
LIBRARY_ROOT = Path(os.environ.get("LIBRARY_ROOT", REPO_ROOT / "agents_library"))

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

SURVEYS_ROOT.mkdir(parents=True, exist_ok=True)
LIBRARY_ROOT.mkdir(parents=True, exist_ok=True)


def survey_dir(survey_id: str) -> Path:
    return SURVEYS_ROOT / survey_id
