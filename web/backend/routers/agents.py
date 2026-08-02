"""Agent Card CRUD and full-trace viewing endpoints."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..paths import CONFIG_DIR, survey_dir

router = APIRouter(prefix="/api", tags=["agents"])

_ID_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$")
KNOWN_PROVIDERS = ["ollama", "anthropic", "openai", "openrouter", "manual"]
DEFAULT_DENYLIST = [
    r"ignore (all|any|the) (previous|prior|above) instructions",
    r"sk-[A-Za-z0-9]{20,}",
    r"-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----",
]
DEFAULT_PROMPT_TEMPLATE = str((CONFIG_DIR / "prompts" / "expert_panel_system.txt").resolve())


def _safe_id(value: str, kind: str = "id") -> str:
    if not _ID_RE.match(value):
        raise HTTPException(400, f"Invalid {kind}: {value!r}. Use letters, digits, '-', '_' only.")
    return value


def _survey_or_404(survey_id: str) -> Path:
    d = survey_dir(_safe_id(survey_id, "survey_id"))
    if not (d / "survey.yaml").exists():
        raise HTTPException(404, f"No survey '{survey_id}'")
    return d


class ModelIn(BaseModel):
    provider: str
    name: str
    temperature: float = 0.7
    max_tokens: int = 1024
    top_p: float = 1.0
    seed: Optional[int] = None


class RagIn(BaseModel):
    enabled: bool = False
    corpus_path: Optional[str] = None
    top_k: int = 5
    embedding_model: Optional[str] = "sentence-transformers/all-MiniLM-L6-v2"
    chunk_size: int = 800
    chunk_overlap: int = 100


class SamplingIn(BaseModel):
    repeats: int = 3
    max_retries_on_malformed: int = 2
    agreement_threshold: float = 0.0


class PermissionsIn(BaseModel):
    data_scopes: List[str] = []
    allowed_providers: Optional[List[str]] = None
    max_cost_usd: Optional[float] = None


class GuardrailsIn(BaseModel):
    denylist_patterns: List[str] = DEFAULT_DENYLIST


class AgentIn(BaseModel):
    agent_id: str
    role: str
    role_description: str
    instrument: str = "bwm"
    system_prompt_template: Optional[str] = None
    model: ModelIn
    rag: RagIn = RagIn()
    sampling: SamplingIn = SamplingIn()
    permissions: PermissionsIn = PermissionsIn()
    guardrails: GuardrailsIn = GuardrailsIn()
    tools: List[str] = []
    did_seed: str = "agentic-survey-tool-default-seed-v1"


def _agent_card_module():
    # Imported lazily so paths.py has already put src/ on sys.path.
    from agentic_survey import agent_card

    return agent_card


@router.get("/providers")
def list_providers() -> List[str]:
    return KNOWN_PROVIDERS


@router.get("/ollama-models")
def list_ollama_models() -> Dict[str, Any]:
    base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    try:
        resp = requests.get(f"{base_url}/api/tags", timeout=5)
        resp.raise_for_status()
        data = resp.json()
        return {"base_url": base_url, "models": [m["name"] for m in data.get("models", [])]}
    except requests.RequestException as exc:
        return {"base_url": base_url, "models": [], "error": str(exc)}


@router.get("/surveys/{survey_id}/agents")
def list_agents(survey_id: str) -> List[Dict[str, Any]]:
    d = _survey_or_404(survey_id)
    ac = _agent_card_module()
    out = []
    for path in sorted((d / "agents").glob("*.json")):
        card = ac.load_card(path)
        out.append(
            {
                "agent_id": card.agent_id,
                "role": card.role,
                "provider": card.model.provider,
                "model": card.model.name,
                "rag_enabled": card.rag.enabled,
                "did": card.did.id,
            }
        )
    return out


@router.get("/surveys/{survey_id}/agents/{agent_id}")
def get_agent(survey_id: str, agent_id: str) -> Dict[str, Any]:
    d = _survey_or_404(survey_id)
    ac = _agent_card_module()
    path = d / "agents" / f"{_safe_id(agent_id, 'agent_id')}.json"
    if not path.exists():
        raise HTTPException(404, f"No agent '{agent_id}' in survey '{survey_id}'")
    return ac.load_card(path).to_dict()


@router.post("/surveys/{survey_id}/agents")
def create_agent(survey_id: str, body: AgentIn) -> Dict[str, Any]:
    d = _survey_or_404(survey_id)
    ac = _agent_card_module()
    agent_id = _safe_id(body.agent_id, "agent_id")
    path = d / "agents" / f"{agent_id}.json"
    if path.exists():
        raise HTTPException(409, f"Agent '{agent_id}' already exists in this survey.")

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
        did_seed=body.did_seed,
    )
    card.write(path)
    return card.to_dict()


@router.put("/surveys/{survey_id}/agents/{agent_id}")
def update_agent(survey_id: str, agent_id: str, body: AgentIn) -> Dict[str, Any]:
    d = _survey_or_404(survey_id)
    ac = _agent_card_module()
    agent_id = _safe_id(agent_id, "agent_id")
    path = d / "agents" / f"{agent_id}.json"
    if not path.exists():
        raise HTTPException(404, f"No agent '{agent_id}' in survey '{survey_id}'")

    existing = ac.load_card(path)  # keep the existing DID; identity doesn't change on edit
    card = ac.AgentCard(
        schema_version=existing.schema_version,
        agent_id=agent_id,
        role=body.role,
        role_description=body.role_description,
        instrument=body.instrument,
        system_prompt_template=body.system_prompt_template or existing.system_prompt_template,
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
    )
    card.write(path)
    return card.to_dict()


@router.delete("/surveys/{survey_id}/agents/{agent_id}")
def delete_agent(survey_id: str, agent_id: str) -> Dict[str, str]:
    d = _survey_or_404(survey_id)
    agent_id = _safe_id(agent_id, "agent_id")
    path = d / "agents" / f"{agent_id}.json"
    if not path.exists():
        raise HTTPException(404, f"No agent '{agent_id}' in survey '{survey_id}'")
    path.unlink()
    runtime_dir = d / "agents" / agent_id
    if runtime_dir.exists():
        import shutil

        shutil.rmtree(runtime_dir)
    return {"status": "deleted"}


@router.get("/surveys/{survey_id}/agents/{agent_id}/trace")
def get_trace(survey_id: str, agent_id: str) -> Dict[str, Any]:
    d = _survey_or_404(survey_id)
    agent_id = _safe_id(agent_id, "agent_id")
    runtime_dir = d / "agents" / agent_id
    if not runtime_dir.exists():
        raise HTTPException(404, f"Agent '{agent_id}' has not been run yet in this survey.")

    def _read(name: str) -> Optional[str]:
        p = runtime_dir / name
        return p.read_text(encoding="utf-8") if p.exists() else None

    conversation = []
    conv_path = runtime_dir / "conversation.jsonl"
    if conv_path.exists():
        for line in conv_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                conversation.append(json.loads(line))

    return {
        "prompt": _read("prompt.md"),
        "thoughts": _read("thoughts.md"),
        "filled_survey": _read("filled_survey.md"),
        "result": json.loads(_read("result.json") or "null"),
        "conversation": conversation,
        "manual_pending": sorted(p.name for p in (runtime_dir / "manual_input").glob("prompt_*.md")) if (runtime_dir / "manual_input").exists() else [],
    }
