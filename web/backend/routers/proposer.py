"""Natural-language agent proposal endpoints: propose (an LLM call, nothing
written to disk) then approve (user-reviewed, now actually create/assign).
Two separate endpoints so a human always reviews and can edit before
anything is materialized. See ../agent_proposer.py's module docstring.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import yaml
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .. import agent_proposer
from ..paths import survey_dir
from .agents import AgentIn, ModelIn, _safe_id

router = APIRouter(prefix="/api/surveys/{survey_id}", tags=["proposer"])


class ProposeIn(BaseModel):
    requirement: str
    provider: str = "ollama"
    model: str


class ProposalEntry(BaseModel):
    source: str  # "library" | "new"
    agent_id: str
    display_name: Optional[str] = None
    expertise: str = ""
    role: Optional[str] = None
    role_description: Optional[str] = None
    model: Optional[ModelIn] = None


class ApproveIn(BaseModel):
    proposals: List[ProposalEntry]


def _survey_context(survey_id: str) -> Dict[str, Any]:
    d = survey_dir(_safe_id(survey_id, "survey_id"))
    survey_yaml = d / "survey.yaml"
    if not survey_yaml.exists():
        raise HTTPException(404, f"No survey '{survey_id}'")
    data = yaml.safe_load(survey_yaml.read_text(encoding="utf-8")) or {}
    return {
        "title": data.get("title", survey_id),
        "description": data.get("description", ""),
        "dimensions": data.get("instrument_params", {}).get("dimensions", []),
    }


@router.post("/propose-agents")
def propose_agents_endpoint(survey_id: str, body: ProposeIn) -> List[Dict[str, Any]]:
    from .library import list_library_agents

    survey_context = _survey_context(survey_id)
    library_agents = list_library_agents()
    try:
        return agent_proposer.propose_agents(
            body.requirement, survey_context, library_agents, body.provider, body.model
        )
    except agent_proposer.ProposalError as exc:
        raise HTTPException(502, f"{exc} Raw response: {exc.raw_text[:800]}") from exc


@router.post("/approve-agents")
def approve_agents_endpoint(survey_id: str, body: ApproveIn) -> List[Dict[str, Any]]:
    """Materializes each approved (and possibly user-edited) proposal:
    "library" entries are assigned into this survey as-is; "new" entries
    are created in the Agent Library first (so they're reusable going
    forward, same as any other library agent) and then assigned. Each
    entry is handled independently and reports its own status/error:
    one bad entry doesn't block the rest, matching how the survey run
    itself never lets one agent's failure take down the whole panel."""
    from .library import assign_to_survey, create_library_agent

    _survey_context(survey_id)  # 404s early if the survey doesn't exist
    results: List[Dict[str, Any]] = []

    for entry in body.proposals:
        try:
            if entry.source == "library":
                card = assign_to_survey(entry.agent_id, survey_id)
                results.append({"status": "assigned", "agent_id": entry.agent_id, "agent": card})
            elif entry.source == "new":
                if not entry.role or not entry.role_description or not entry.model:
                    raise HTTPException(400, "New agent is missing role, role_description, or model.")
                agent_body = AgentIn(
                    agent_id=entry.agent_id,
                    role=entry.role,
                    role_description=entry.role_description,
                    display_name=entry.display_name,
                    expertise=entry.expertise,
                    model=entry.model,
                )
                create_library_agent(agent_body)
                assigned_card = assign_to_survey(entry.agent_id, survey_id)
                results.append({"status": "created_and_assigned", "agent_id": entry.agent_id, "agent": assigned_card})
            else:
                raise HTTPException(400, f"Unknown source {entry.source!r}; must be 'library' or 'new'.")
        except HTTPException as exc:
            results.append({"status": "error", "agent_id": entry.agent_id, "detail": exc.detail})

    return results
