"""Agent spawning: mint a child identity, attenuate its capabilities, and
declare the spawn before the agent does anything else.

Two spawn shapes exist, both writing the same `spawn_declaration.json`
contract (see `docs/architecture/governance-layer-and-runtime-backends-plan.md`
§5):

- **Root spawn** (`declare_root`): today's actual usage. Every agent in a
  survey's flat panel is pre-authored (its Agent Card, and the DID inside
  it, already exist before the run starts, minted by `agent_card.new_card`
  at authoring time). No new identity is minted here; this only records the
  runtime fact "this already-identified agent is being spawned now, by the
  orchestrator, with these capabilities" as that agent's first trail entry.
- **Child spawn** (`mint_child` + `declare_child`): not yet wired into
  `orchestrator.py`'s flat-panel loop (Symphysis has no agent-spawns-agent
  flow yet), but fully implemented and tested here ahead of the OpenManus
  multi-agent flow work that will use it. A parent agent's own identity
  mints a fresh child DID and issues a Verifiable Credential attesting to
  the spawn; the child's granted capabilities are the intersection of the
  parent's own granted capabilities and what the child requested, per
  `policy/capability.py::attenuate`. A child can never exceed the
  authority of the agent that spawned it.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from ..identity.did import AgentIdentity
from ..policy import capability as capability_module
from . import lineage

if TYPE_CHECKING:
    from ..agent_card import AgentCard, ModelSpec
    from ..audit.logger import SurveyStorage


@dataclass
class SpawnCredential:
    """Returned by `mint_child`: the newly minted identity plus the
    Verifiable Credential its parent issued attesting to the spawn. The
    caller (whatever drives a multi-agent flow) decides how the credential
    is surfaced (embedded in the declaration, handed to the child, etc.);
    minting itself does no I/O."""

    identity: AgentIdentity
    credential: Dict[str, Any]


def _model_dict(model: "ModelSpec") -> Dict[str, Any]:
    return {"provider": model.provider, "name": model.name, "temperature": model.temperature}


def _write_declaration(storage: "SurveyStorage", agent_id: str, declaration: Dict[str, Any]) -> None:
    d = storage.agent_dir(agent_id)
    (d / "spawn_declaration.json").write_text(json.dumps(declaration, indent=2), encoding="utf-8")
    # Also appended to the conversation trace, so a reviewer scanning
    # conversation.jsonl (already this agent's canonical event-by-event
    # record) sees the spawn declared before anything else, exactly as
    # storage.write_qa_precheck already makes the QA precheck that agent's
    # first logged event.
    storage.append_conversation(agent_id, {"kind": "spawn_declared", **declaration})


def declare_root(
    storage: "SurveyStorage",
    card: "AgentCard",
    *,
    survey_id: str,
    runtime_backend: str = "ollama",
) -> Dict[str, Any]:
    """Declares a pre-authored, already-identified agent's spawn as a root
    spawn (`parent_did=None`): today's actual orchestrator usage. Requested
    and granted capabilities are identical for a root spawn (there is no
    parent to attenuate against; the real ceiling is the survey's own
    PermissionsSpec, enforced separately and unchanged by
    `policy/authorization.py`'s existing checks)."""
    requested = capability_module.capabilities_from_card(card)
    declaration = {
        "agent_id": card.agent_id,
        "did": card.did.id,
        "parent_did": None,
        "spawned_by": "orchestrator",
        "role": card.role,
        "capabilities_requested": requested,
        "capabilities_granted": list(requested),
        "model": _model_dict(card.model),
        "runtime_backend": runtime_backend,
        "survey_id": survey_id,
    }
    _write_declaration(storage, card.agent_id, declaration)
    lineage.append(storage, child_did=card.did.id, child_agent_id=card.agent_id, parent_did=None)
    return declaration


def mint_child(
    parent: AgentIdentity,
    child_agent_id: str,
    *,
    deterministic: bool = True,
    seed: Optional[str] = None,
    spawn_id: Optional[str] = None,
) -> SpawnCredential:
    """Mints a fresh child identity and has the parent sign a Verifiable
    Credential over it. `seed` defaults to a value derived from the
    parent's own DID plus the child's agent_id, so a deterministic child
    spawned twice by the same parent for the same agent_id reproduces the
    identical DID (the same reproducibility property `AgentCard.new_card`
    already gives root agents), without requiring the caller to invent and
    track a seed of its own."""
    identity = (
        AgentIdentity.generate_deterministic(child_agent_id, seed or f"{parent.did}:{child_agent_id}")
        if deterministic
        else AgentIdentity.generate_random(child_agent_id)
    )
    credential = parent.issue_credential(
        "AgentSpawn", {"childDid": identity.did, "childAgentId": child_agent_id}, spawn_id=spawn_id
    )
    return SpawnCredential(identity=identity, credential=credential)


def declare_child(
    storage: "SurveyStorage",
    *,
    child: SpawnCredential,
    child_agent_id: str,
    role: str,
    parent: AgentIdentity,
    parent_granted_capabilities: List[str],
    capabilities_requested: List[str],
    model: "ModelSpec",
    survey_id: str,
    runtime_backend: str,
) -> Dict[str, Any]:
    """Declares a freshly minted child's spawn. Capabilities are attenuated
    (intersection, never union, per `policy/capability.py::attenuate`)
    before being written, so the declaration itself is the enforcement
    record, not just documentation of an intended limit."""
    granted = capability_module.attenuate(parent_granted_capabilities, capabilities_requested)
    declaration = {
        "agent_id": child_agent_id,
        "did": child.identity.did,
        "parent_did": parent.did,
        "spawned_by": f"agent:{parent.agent_id}",
        "role": role,
        "capabilities_requested": capabilities_requested,
        "capabilities_granted": granted,
        "model": _model_dict(model),
        "runtime_backend": runtime_backend,
        "survey_id": survey_id,
        "spawn_credential": child.credential,
    }
    _write_declaration(storage, child_agent_id, declaration)
    lineage.append(storage, child_did=child.identity.did, child_agent_id=child_agent_id, parent_did=parent.did)
    return declaration
