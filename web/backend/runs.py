"""In-process background-run tracker.

A survey run calls real LLMs and a PyMC sampler, both slow enough that they
must not block the request/response cycle. This is a single-process,
in-memory tracker (a dict + a thread per run) -- adequate for one person
running this as an internal tool, not a distributed job queue.
"""

from __future__ import annotations

import threading
import traceback
from pathlib import Path
from typing import Any, Dict, Optional

_STATUS: Dict[str, Dict[str, Any]] = {}
_LOCK = threading.Lock()


def set_status(survey_id: str, status: str, message: Optional[str] = None) -> None:
    with _LOCK:
        _STATUS[survey_id] = {"status": status, "message": message}


def get_status(survey_id: str) -> Dict[str, Any]:
    with _LOCK:
        return dict(_STATUS.get(survey_id, {"status": "idle", "message": None}))


def start_run(survey_id: str, survey_root: Path) -> None:
    current = get_status(survey_id)
    if current["status"] == "running":
        raise RuntimeError(f"Survey '{survey_id}' is already running.")

    def _run() -> None:
        set_status(survey_id, "running")
        try:
            from agentic_survey.config import load_survey_config
            from agentic_survey.orchestrator import run_survey

            survey = load_survey_config(survey_root)
            run_survey(survey)
            set_status(survey_id, "complete")
        except Exception as exc:  # noqa: BLE001 - report to the UI, don't crash the server
            set_status(survey_id, "error", message=f"{exc}\n\n{traceback.format_exc()}")

    thread = threading.Thread(target=_run, daemon=True, name=f"survey-run-{survey_id}")
    thread.start()
