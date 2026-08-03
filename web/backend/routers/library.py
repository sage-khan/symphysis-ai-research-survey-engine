"""Agent Library: reusable Agent Cards not tied to any one survey.

"Assigning" a library agent to a survey materializes (copies) its card into
that survey's own agents/ directory. The orchestrator/storage/run
pipeline only ever reads surveys/<id>/agents/*.json, so library agents
themselves are never run directly; a library entry is a reusable
template/registry entry that a survey pulls a copy of, keeping the exact
same agent_id and did:key identity as the library original. This mirrors
this app's own stated Agent Card philosophy ("give someone this JSON and
they can respawn an identical agent, anywhere") rather than inventing a
second identity concept.

Reuses agents.py's request models and helpers (AgentIn and friends) rather
than duplicating ~80 lines of Pydantic schema: library and survey-scoped
agents are the exact same Agent Card shape, just rooted in a different
directory.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from ..paths import LIBRARY_ROOT, survey_dir
from .agents import DEFAULT_PROMPT_TEMPLATE, AgentIn, _agent_card_module, _safe_id

router = APIRouter(prefix="/api/library", tags=["library"])


def _library_path(agent_id: str) -> Path:
    return LIBRARY_ROOT / f"{_safe_id(agent_id, 'agent_id')}.json"


def _summary(card) -> Dict[str, Any]:
    return {
        "agent_id": card.agent_id,
        "display_name": card.display_name,
        "expertise": card.expertise,
        "role_pack": card.role_pack,
        "rulefile": card.rulefile,
        "role": card.role,
        "role_description": card.role_description,
        "provider": card.model.provider,
        "model": card.model.name,
        "rag_enabled": card.rag.enabled,
        "tools": card.tools,
        "did": card.did.id,
    }


@router.get("/agents")
def list_library_agents() -> List[Dict[str, Any]]:
    ac = _agent_card_module()
    return [_summary(ac.load_card(path)) for path in sorted(LIBRARY_ROOT.glob("*.json"))]


@router.get("/agents/{agent_id}")
def get_library_agent(agent_id: str) -> Dict[str, Any]:
    ac = _agent_card_module()
    path = _library_path(agent_id)
    if not path.exists():
        raise HTTPException(404, f"No library agent '{agent_id}'")
    return ac.load_card(path).to_dict()


@router.post("/agents")
def create_library_agent(body: AgentIn) -> Dict[str, Any]:
    ac = _agent_card_module()
    agent_id = _safe_id(body.agent_id, "agent_id")
    path = _library_path(agent_id)
    if path.exists():
        raise HTTPException(409, f"Library agent '{agent_id}' already exists.")

    card = ac.new_card(
        agent_id=agent_id,
        role=body.role,
        role_description=body.role_description,
        system_prompt_template=body.system_prompt_template or DEFAULT_PROMPT_TEMPLATE,
        model=ac.ModelSpec(**body.model.model_dump()),
        instrument=body.instrument,
        rag=ac.RagSpec(**body.rag.model_dump()),
        sampling=ac.SamplingSpec(**body.sampling.model_dump()),
        permissions=ac.PermissionsSpec(
            data_scopes=body.permissions.data_scopes,
            allowed_providers=body.permissions.allowed_providers or [body.model.provider],
            max_cost_usd=body.permissions.max_cost_usd,
        ),
        guardrails=ac.GuardrailsSpec(denylist_patterns=body.guardrails.denylist_patterns),
        tools=body.tools,
        display_name=body.display_name,
        expertise=body.expertise,
        role_pack=body.role_pack,
        rulefile=body.rulefile,
        system_prompt_override=body.system_prompt_override or None,
        did_seed=body.did_seed,
    )
    card.write(path)
    return card.to_dict()


@router.put("/agents/{agent_id}")
def update_library_agent(agent_id: str, body: AgentIn) -> Dict[str, Any]:
    ac = _agent_card_module()
    agent_id = _safe_id(agent_id, "agent_id")
    path = _library_path(agent_id)
    if not path.exists():
        raise HTTPException(404, f"No library agent '{agent_id}'")

    existing = ac.load_card(path)  # keep the existing DID; identity doesn't change on edit
    card = ac.AgentCard(
        schema_version=existing.schema_version,
        agent_id=agent_id,
        role=body.role,
        role_description=body.role_description,
        instrument=body.instrument,
        system_prompt_template=body.system_prompt_template or existing.system_prompt_template,
        system_prompt_override=body.system_prompt_override or None,
        model=ac.ModelSpec(**body.model.model_dump()),
        rag=ac.RagSpec(**body.rag.model_dump()),
        sampling=ac.SamplingSpec(**body.sampling.model_dump()),
        permissions=ac.PermissionsSpec(
            data_scopes=body.permissions.data_scopes,
            allowed_providers=body.permissions.allowed_providers or [body.model.provider],
            max_cost_usd=body.permissions.max_cost_usd,
        ),
        guardrails=ac.GuardrailsSpec(denylist_patterns=body.guardrails.denylist_patterns),
        did=existing.did,
        environment=existing.environment,
        tools=body.tools,
        display_name=body.display_name,
        expertise=body.expertise,
        role_pack=body.role_pack,
        rulefile=body.rulefile,
    )
    card.write(path)
    return card.to_dict()


@router.delete("/agents/{agent_id}")
def delete_library_agent(agent_id: str) -> Dict[str, str]:
    path = _library_path(agent_id)
    if not path.exists():
        raise HTTPException(404, f"No library agent '{agent_id}'")
    path.unlink()
    return {"status": "deleted"}


@router.post("/agents/{agent_id}/assign/{survey_id}")
def assign_to_survey(agent_id: str, survey_id: str) -> Dict[str, Any]:
    """Copy this library agent's card into the given survey's agents/
    directory, keeping the same agent_id and did:key identity, so the
    orchestrator picks it up on the survey's next run. Refuses if the
    survey already has an agent with this id (use the survey's own Agents
    tab to edit that copy instead; the two are independent files once
    copied, matching how every other Agent Card in this app works)."""
    ac = _agent_card_module()
    src_path = _library_path(agent_id)
    if not src_path.exists():
        raise HTTPException(404, f"No library agent '{agent_id}'")

    d = survey_dir(_safe_id(survey_id, "survey_id"))
    if not (d / "survey.yaml").exists():
        raise HTTPException(404, f"No survey '{survey_id}'")

    dest_path = d / "agents" / f"{agent_id}.json"
    if dest_path.exists():
        raise HTTPException(409, f"Survey '{survey_id}' already has an agent '{agent_id}'.")

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    card = ac.load_card(src_path)
    card.write(dest_path)
    return card.to_dict()
