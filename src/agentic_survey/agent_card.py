"""The Agent Card: one portable JSON file that fully defines a spawnable
agent.

This is the single-file "agent spec" that project-cogtwins's own design
docs (URD Amendment v2.0 S19, "Agent Identity & Policy Enforcement")
describe wanting but never built -- that project's agents are Python
objects assembled from a hardcoded registry plus two small config tables,
not a portable file anyone can pick up and replicate. An Agent Card closes
that gap: give someone this JSON (and, if the DID is deterministic, the
shared master seed) and they can respawn an identical agent, anywhere,
without reading this app's source.

Every field that shapes agent behaviour lives in the card. Nothing about
prompts, hyperparameters, permissions, or identity is hardcoded in Python.
"""

from __future__ import annotations

import json
import platform
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import __version__ as RUNTIME_VERSION
from . import app_config
from .did_key import AgentIdentity

SCHEMA_VERSION = "1.0"


class AgentCardError(Exception):
    pass


def _model_default(key: str, fallback: Any) -> Any:
    # Read through app_config (config/defaults.yaml, overridable via
    # Settings -> Config) rather than a literal, so changing the default
    # for newly-created agents never requires a code change. `fallback`
    # only applies if the config file itself is missing/unreadable.
    return app_config.model_defaults().get(key, fallback)


def _sampling_default(key: str, fallback: Any) -> Any:
    return app_config.sampling_defaults().get(key, fallback)


def _rag_default(key: str, fallback: Any) -> Any:
    return app_config.rag_defaults().get(key, fallback)


@dataclass
class ModelSpec:
    provider: str
    name: str
    temperature: float = field(default_factory=lambda: _model_default("temperature", 0.7))
    max_tokens: int = field(default_factory=lambda: _model_default("max_tokens", 1024))
    top_p: float = field(default_factory=lambda: _model_default("top_p", 1.0))
    seed: Optional[int] = field(default_factory=lambda: _model_default("seed", None))
    model_hash: Optional[str] = None  # optional content/digest binding, if the provider reports one


@dataclass
class RagSpec:
    enabled: bool = False
    corpus_path: Optional[str] = None
    top_k: int = field(default_factory=lambda: _rag_default("top_k", 5))
    embedding_model: Optional[str] = field(default_factory=lambda: _rag_default("embedding_model", None))
    chunk_size: int = field(default_factory=lambda: _rag_default("chunk_size", 800))
    chunk_overlap: int = field(default_factory=lambda: _rag_default("chunk_overlap", 100))


@dataclass
class SamplingSpec:
    repeats: int = field(default_factory=lambda: _sampling_default("repeats", 3))
    max_retries_on_malformed: int = field(default_factory=lambda: _sampling_default("max_retries_on_malformed", 2))
    agreement_threshold: float = field(default_factory=lambda: _sampling_default("agreement_threshold", 0.0))


@dataclass
class PermissionsSpec:
    """What this agent may touch. Enforced by guardrails.py, not advisory."""

    data_scopes: List[str] = field(default_factory=list)   # glob patterns this agent's RAG/reads may match
    network: List[str] = field(default_factory=list)        # allowed outbound hosts, informational + checked by providers
    allowed_providers: List[str] = field(
        default_factory=lambda: ["ollama", "anthropic", "openai", "openrouter", "groq", "gemini", "xai", "manual"]
    )
    max_cost_usd: Optional[float] = None


@dataclass
class GuardrailsSpec:
    schema_validation: bool = True
    denylist_patterns: List[str] = field(default_factory=list)  # regex; raw output must not match any


@dataclass
class DidSpec:
    method: str            # "did:key"
    id: str
    public_key_multibase: str
    deterministic: bool
    seed_derivation: Optional[str] = None  # human-readable description of how the seed was formed, if deterministic


@dataclass
class EnvironmentSpec:
    runtime: str = "symphysis"
    runtime_version: str = RUNTIME_VERSION
    python_version: str = field(default_factory=platform.python_version)
    platform: str = field(default_factory=platform.platform)
    container_image: Optional[str] = None


@dataclass
class AgentCard:
    schema_version: str
    agent_id: str
    role: str
    role_description: str
    instrument: str
    system_prompt_template: str
    model: ModelSpec
    rag: RagSpec
    sampling: SamplingSpec
    permissions: PermissionsSpec
    guardrails: GuardrailsSpec
    did: DidSpec
    environment: EnvironmentSpec
    tools: List[str] = field(default_factory=list)
    display_name: Optional[str] = None  # human-facing name shown in the UI; falls back to role/agent_id if unset
    expertise: str = ""  # short structured profession/expertise line, distinct from the narrative role_description
    system_prompt_override: Optional[str] = None  # literal system-prompt text; takes precedence over system_prompt_template

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "agent_id": self.agent_id,
            "role": self.role,
            "display_name": self.display_name,
            "expertise": self.expertise,
            "role_description": self.role_description,
            "instrument": self.instrument,
            "system_prompt_template": self.system_prompt_template,
            "system_prompt_override": self.system_prompt_override,
            "tools": self.tools,
            "model": vars(self.model),
            "rag": vars(self.rag),
            "sampling": vars(self.sampling),
            "permissions": vars(self.permissions),
            "guardrails": vars(self.guardrails),
            "did": vars(self.did),
            "environment": vars(self.environment),
        }

    def write(self, path: Path) -> None:
        path.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=False), encoding="utf-8")


def new_card(
    agent_id: str,
    role: str,
    role_description: str,
    system_prompt_template: str,
    model: ModelSpec,
    *,
    instrument: str = "bwm",
    rag: Optional[RagSpec] = None,
    sampling: Optional[SamplingSpec] = None,
    permissions: Optional[PermissionsSpec] = None,
    guardrails: Optional[GuardrailsSpec] = None,
    tools: Optional[List[str]] = None,
    display_name: Optional[str] = None,
    expertise: str = "",
    system_prompt_override: Optional[str] = None,
    deterministic_did: bool = True,
    did_seed: str = "agentic-survey-tool-default-seed-v1",
) -> AgentCard:
    """Build a fresh AgentCard, generating its DID now. Callers that want a
    reproducible DID across machines must pass the same did_seed and
    agent_id; the seed is recorded (as a derivation description, not the raw
    seed itself) in the card so a reader can see exactly how the DID was
    derived, not just what it is."""

    identity = (
        AgentIdentity.generate_deterministic(agent_id, did_seed)
        if deterministic_did
        else AgentIdentity.generate_random(agent_id)
    )

    return AgentCard(
        schema_version=SCHEMA_VERSION,
        agent_id=agent_id,
        role=role,
        role_description=role_description,
        instrument=instrument,
        system_prompt_template=system_prompt_template,
        model=model,
        rag=rag or RagSpec(),
        sampling=sampling or SamplingSpec(),
        permissions=permissions or PermissionsSpec(),
        guardrails=guardrails or GuardrailsSpec(),
        tools=tools or [],
        display_name=display_name,
        expertise=expertise,
        system_prompt_override=system_prompt_override,
        did=DidSpec(
            method="did:key",
            id=identity.did,
            public_key_multibase=identity.public_key_multibase,
            deterministic=identity.deterministic,
            seed_derivation=(f"sha256('{did_seed}:{agent_id}')" if deterministic_did else None),
        ),
        environment=EnvironmentSpec(),
    )


def load_card(path: Path) -> AgentCard:
    if not path.exists():
        raise AgentCardError(f"Agent card not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))

    for required in ("schema_version", "agent_id", "role", "role_description", "instrument",
                      "system_prompt_template", "model", "did"):
        if required not in data:
            raise AgentCardError(f"Agent card {path} missing required field '{required}'")
    if data["schema_version"] != SCHEMA_VERSION:
        raise AgentCardError(
            f"Agent card {path} has schema_version={data['schema_version']!r}, "
            f"this runtime supports {SCHEMA_VERSION!r}"
        )

    return AgentCard(
        schema_version=data["schema_version"],
        agent_id=data["agent_id"],
        role=data["role"],
        role_description=data["role_description"],
        instrument=data["instrument"],
        system_prompt_template=data["system_prompt_template"],
        tools=data.get("tools", []),
        display_name=data.get("display_name"),
        expertise=data.get("expertise", ""),
        system_prompt_override=data.get("system_prompt_override"),
        model=ModelSpec(**data["model"]),
        rag=RagSpec(**data.get("rag", {})),
        sampling=SamplingSpec(**data.get("sampling", {})),
        permissions=PermissionsSpec(**data.get("permissions", {})),
        guardrails=GuardrailsSpec(**data.get("guardrails", {})),
        did=DidSpec(**data["did"]),
        environment=EnvironmentSpec(**data.get("environment", {})),
    )


def rehydrate_identity(card: AgentCard, did_seed: Optional[str] = None) -> AgentIdentity:
    """Reconstruct the signing identity from a loaded card. For a
    deterministic card this requires the same seed used to create it (the
    card documents the derivation but, correctly, does not store the seed
    itself -- that would defeat the point of a keyed derivation)."""
    if not card.did.deterministic:
        raise AgentCardError(
            f"Card {card.agent_id} has a randomly generated DID; its private key was never persisted "
            "and cannot be rehydrated from the card. Only its public DID/credentials remain verifiable."
        )
    if not did_seed:
        raise AgentCardError(
            f"Card {card.agent_id} has a deterministic DID; pass the matching did_seed to respawn its identity."
        )
    identity = AgentIdentity.generate_deterministic(card.agent_id, did_seed)
    if identity.did != card.did.id:
        raise AgentCardError(
            f"Rehydrated DID {identity.did} does not match card's recorded DID {card.did.id}; "
            "wrong seed, or the card was hand-edited."
        )
    return identity
