"""Agent Card CRUD and full-trace viewing endpoints."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..paths import CONFIG_DIR, survey_dir

router = APIRouter(prefix="/api", tags=["agents"])

_ID_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$")
KNOWN_PROVIDERS = ["ollama", "anthropic", "openai", "openrouter", "groq", "gemini", "xai", "manual"]
DEFAULT_PROMPT_TEMPLATE = str((CONFIG_DIR / "prompts" / "expert_panel_system.txt").resolve())


def _cfg():
    # Imported lazily, same reason as _agent_card_module() below: paths.py
    # must have already put src/ on sys.path.
    from symphysis import app_config

    return app_config


def _default_denylist() -> List[str]:
    configured = _cfg().guardrail_default_denylist()
    return configured or [
        r"ignore (all|any|the) (previous|prior|above) instructions",
        r"sk-[A-Za-z0-9]{20,}",
        r"-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----",
    ]


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
    temperature: float = Field(default_factory=lambda: _cfg().model_defaults().get("temperature", 0.7))
    max_tokens: int = Field(default_factory=lambda: _cfg().model_defaults().get("max_tokens", 1024))
    top_p: float = Field(default_factory=lambda: _cfg().model_defaults().get("top_p", 1.0))
    seed: Optional[int] = Field(default_factory=lambda: _cfg().model_defaults().get("seed"))


class RagIn(BaseModel):
    enabled: bool = False
    corpus_path: Optional[str] = None
    top_k: int = Field(default_factory=lambda: _cfg().rag_defaults().get("top_k", 5))
    embedding_model: Optional[str] = Field(
        default_factory=lambda: _cfg().rag_defaults().get("embedding_model", "sentence-transformers/all-MiniLM-L6-v2")
    )
    chunk_size: int = Field(default_factory=lambda: _cfg().rag_defaults().get("chunk_size", 800))
    chunk_overlap: int = Field(default_factory=lambda: _cfg().rag_defaults().get("chunk_overlap", 100))


class SamplingIn(BaseModel):
    repeats: int = Field(default_factory=lambda: _cfg().sampling_defaults().get("repeats", 3))
    max_retries_on_malformed: int = Field(
        default_factory=lambda: _cfg().sampling_defaults().get("max_retries_on_malformed", 2)
    )
    agreement_threshold: float = Field(
        default_factory=lambda: _cfg().sampling_defaults().get("agreement_threshold", 0.0)
    )


class PermissionsIn(BaseModel):
    data_scopes: List[str] = []
    allowed_providers: Optional[List[str]] = None
    max_cost_usd: Optional[float] = None


class GuardrailsIn(BaseModel):
    denylist_patterns: List[str] = Field(default_factory=_default_denylist)


class AgentIn(BaseModel):
    agent_id: str
    role: str
    display_name: Optional[str] = None
    expertise: str = ""
    role_pack: Optional[str] = None
    rulefile: str = ""
    role_description: str
    instrument: str = "bwm"
    system_prompt_template: Optional[str] = None
    system_prompt_override: Optional[str] = None
    model: ModelIn
    rag: RagIn = RagIn()
    sampling: SamplingIn = SamplingIn()
    permissions: PermissionsIn = PermissionsIn()
    guardrails: GuardrailsIn = GuardrailsIn()
    tools: List[str] = []
    did_seed: str = "agentic-survey-tool-default-seed-v1"


def _agent_card_module():
    # Imported lazily so paths.py has already put src/ on sys.path.
    from symphysis import agent_card

    return agent_card


@router.get("/providers")
def list_providers() -> List[str]:
    return KNOWN_PROVIDERS


@router.get("/models/{provider}")
def list_models_for_provider(provider: str) -> Dict[str, Any]:
    """The live, real model list for `provider`: Ollama's own /api/tags,
    or each hosted provider's own list-models API, never a hardcoded or
    guessed list. Every model picker in the UI reads through this, so a
    user can only select a model that's actually confirmed available."""
    from ..model_catalog import list_models

    return list_models(provider)


@router.get("/role-packs")
def list_role_packs() -> List[Dict[str, str]]:
    """Standard professional-domain knowledge packs available to attach to
    an agent (see symphysis/role_packs/), discovered from disk, so
    the picker always reflects exactly what packs actually ship."""
    from symphysis import role_packs

    return role_packs.list_role_packs()


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
                "display_name": card.display_name,
                "expertise": card.expertise,
                "role_pack": card.role_pack,
                "rulefile": card.rulefile,
                "role": card.role,
                "provider": card.model.provider,
                "model": card.model.name,
                "rag_enabled": card.rag.enabled,
                "tools": card.tools,
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
        display_name=body.display_name,
        expertise=body.expertise,
        role_pack=body.role_pack,
        rulefile=body.rulefile,
        system_prompt_override=body.system_prompt_override or None,
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
