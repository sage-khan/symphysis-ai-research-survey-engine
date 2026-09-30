"""Survey-level config loading and validation.

Per-agent config now lives entirely in agent_card.py's AgentCard (portable
JSON, one file per agent, see agents/*.json under a survey directory). This
module only owns the survey manifest (survey.yaml): which instrument, which
dimensions, and the HAWC-BWM weighting/sensitivity-sweep settings, things
that describe the survey as a whole, not any one agent.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

import yaml


class ConfigError(Exception):
    """Raised when a survey config fails validation."""


@dataclass
class SurveyConfig:
    id: str
    title: str
    instrument: str
    instrument_params: Dict[str, Any]
    weighting: Dict[str, Any]
    root: Path
    agent_cards: List[Path]
    description: str = ""
    created_at: str = ""
    # Phase 4 model-tiering (docs/architecture/governance-layer-and-runtime-backends-plan.md):
    # {} (the default, and every survey.yaml written before this field
    # existed) means "no escalation" — stays local-first. Shape when set:
    # {"threshold": 6, "model": {"provider": ..., "name": ..., "temperature": ...,
    #  "max_tokens": ..., "top_p": ...}}. See policy/engine.py::escalated_level_ids.
    escalation: Dict[str, Any] = field(default_factory=dict)


def _read_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ConfigError(f"Config file did not parse to a mapping: {path}")
    return data


def load_survey_config(survey_dir: Path) -> SurveyConfig:
    survey_yaml = survey_dir / "survey.yaml"
    data = _read_yaml(survey_yaml)
    for required in ("id", "title", "instrument"):
        if required not in data:
            raise ConfigError(f"Survey config {survey_yaml} missing required field '{required}'")

    agents_dir = survey_dir / "agents"
    agent_cards = sorted(agents_dir.glob("*.json")) if agents_dir.exists() else []
    if not agent_cards:
        raise ConfigError(f"No agent cards (*.json) found under {agents_dir}")

    return SurveyConfig(
        id=data["id"],
        title=data["title"],
        instrument=data["instrument"],
        instrument_params=data.get("instrument_params", {}) or {},
        weighting=data.get("weighting", {}) or {},
        root=survey_dir,
        agent_cards=agent_cards,
        description=data.get("description", "") or "",
        created_at=data.get("created_at", "") or "",
        escalation=data.get("escalation", {}) or {},
    )
