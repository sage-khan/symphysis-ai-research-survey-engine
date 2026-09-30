"""Pipeline stages: named, config-driven meta-agents that review a survey's
own setup or its panel's own responses, distinct from the panel of agents
that actually answers the survey instrument.

A stage is enabled per-survey via `survey.yaml`'s optional `pipeline:` key,
e.g. `{"setup_review": {"agent_card": "pipeline_agents/setup-fixer.json"}}`.
An absent key means that stage does not run — every survey.yaml written
before this module existed behaves exactly as before. Each stage's Agent
Card is authored exactly like a panel agent's own card (its own model,
prompt, permissions); nothing about a stage's behavior is hardcoded here.

Every stage agent is a genuine child spawn (`spawning/spawn.py::mint_child`/
`declare_child`), not a second root spawn: `_pipeline_root_identity()` is a
deterministic identity representing this survey's own pipeline invocation,
and every stage's granted capabilities are attenuated (intersected, never
unioned) against `PIPELINE_ROOT_CAPABILITIES` below. This produces a real,
inspectable two-level lineage tree (`lineage.json`: pipeline-orchestrator ->
setup-fixer, pipeline-orchestrator -> response-reviewer, ...) rather than
reusing the flat root-spawn shape every panel agent already uses.

A stage failing (a bad card, an uncredentialed provider, a review agent that
never produces a schema-valid response) is reported, never fatal to the
survey it was meant to review — the same "skip and keep going" philosophy
`orchestrator.py::run_survey()` already applies to a misconfigured panel
agent.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from ..agent import Agent
from ..agent_card import AgentCardError, load_card
from ..audit.logger import SurveyStorage
from ..config import SurveyConfig
from ..identity.did import AgentIdentity
from ..instruments.response_review import ResponseReviewInstrument
from ..instruments.setup_review import SetupReviewInstrument
from ..policy import capability as capability_module
from ..policy.authorization import PermissionError_
from ..providers.base import ProviderError
from ..runtime.openmanus import OpenManusProviderError
from ..survey_checks import fix_survey
from . import spawn as agent_spawn

PIPELINE_ROOT_AGENT_ID = "pipeline-orchestrator"

# The capability ceiling every pipeline-stage agent is attenuated against.
# Deliberately excludes SPAWN_CHILD (no stage spawns a further child in this
# version) and the Phase-5-deferred code_execution/filesystem_write
# capabilities (policy/capability.py): a pipeline stage can hold exactly the
# same grounding capabilities a direct-completion panel agent already can.
PIPELINE_ROOT_CAPABILITIES: List[str] = [
    capability_module.RAG_RETRIEVAL,
    capability_module.WEB_SEARCH,
    capability_module.KNOWLEDGE_REPO,
]

_KNOWN_ERRORS = (ProviderError, PermissionError_, AgentCardError, OpenManusProviderError, FileNotFoundError)


def _pipeline_root_identity(survey: SurveyConfig) -> AgentIdentity:
    """Deterministic per survey, never itself declared as a spawn or run:
    this identity exists only to be the parent a stage's child spawn is
    attenuated against, the same role `orchestrator.py` itself plays for a
    root spawn today, made concrete as a real AgentIdentity so
    `spawn.py::mint_child` has a parent to sign the child's credential."""
    return AgentIdentity.generate_deterministic(PIPELINE_ROOT_AGENT_ID, f"symphysis-pipeline:{survey.id}")


def _spawn_stage_agent(storage: SurveyStorage, survey: SurveyConfig, stage_role: str, card_path: Path) -> Agent:
    card = load_card(card_path)
    parent = _pipeline_root_identity(survey)
    requested = capability_module.capabilities_from_card(card)
    credential = agent_spawn.mint_child(parent, card.agent_id)
    agent_spawn.declare_child(
        storage,
        child=credential,
        child_agent_id=card.agent_id,
        role=stage_role,
        parent=parent,
        parent_granted_capabilities=PIPELINE_ROOT_CAPABILITIES,
        capabilities_requested=requested,
        model=card.model,
        survey_id=survey.id,
        runtime_backend=card.runtime_backend,
    )
    return Agent(card, card_path, storage)


def run_setup_review(survey: SurveyConfig, storage: SurveyStorage) -> Optional[Dict[str, Any]]:
    """Runs the setup_review stage if `survey.pipeline` declares one.
    Returns its findings payload, `None` if the stage isn't configured, or a
    dict with an `"error"` key (never raises) if the stage agent itself
    couldn't produce a valid response."""
    stage = survey.pipeline.get("setup_review")
    if not stage:
        return None

    card_path = survey.root / stage["agent_card"]
    problems = fix_survey(survey.root)
    survey_yaml_text = (survey.root / "survey.yaml").read_text(encoding="utf-8")
    agent_cards_text = [p.read_text(encoding="utf-8") for p in survey.agent_cards]

    try:
        agent = _spawn_stage_agent(storage, survey, "setup_review", card_path)
        run = agent.run(
            SetupReviewInstrument(),
            {
                "deterministic_problems": problems,
                "survey_yaml_text": survey_yaml_text,
                "agent_cards_text": agent_cards_text,
            },
            survey_title=survey.title,
            survey_description=survey.description,
        )
    except _KNOWN_ERRORS as exc:
        return {"error": f"{type(exc).__name__}: {exc}"}

    if not run.accepted:
        return {"error": "setup_review agent produced no schema-valid response; see its own conversation log"}
    return run.accepted[0].payload


def run_response_review(
    survey: SurveyConfig,
    storage: SurveyStorage,
    per_agent_detail: List[Dict[str, Any]],
    codes: List[str],
) -> Optional[Dict[str, Any]]:
    """Runs the response_review stage if `survey.pipeline` declares one,
    reviewing the panel's own already-accepted per-agent answers. Same
    never-raises contract as `run_setup_review`."""
    stage = survey.pipeline.get("response_review")
    if not stage:
        return None

    card_path = survey.root / stage["agent_card"]
    agent_responses = [
        {"agent_id": d["agent_id"], "role": d["role"], "answer": d["answer"], "reasoning": d["reasoning"]}
        for d in per_agent_detail
    ]

    try:
        agent = _spawn_stage_agent(storage, survey, "response_review", card_path)
        run = agent.run(
            ResponseReviewInstrument(),
            {
                "survey_title": survey.title,
                "instrument": survey.instrument,
                "dimensions": codes,
                "agent_responses": agent_responses,
            },
            survey_title=survey.title,
            survey_description=survey.description,
        )
    except _KNOWN_ERRORS as exc:
        return {"error": f"{type(exc).__name__}: {exc}"}

    if not run.accepted:
        return {"error": "response_review agent produced no schema-valid response; see its own conversation log"}
    return run.accepted[0].payload
