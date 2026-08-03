"""Survey-level "fix-survey" pre-check: static validation of a survey
project folder (survey.yaml + agents/*.json) before a real run, so a
misconfigured hierarchy, a stale RAG corpus path, or a dangling role_pack
id is reported as a plain list of problems up front, instead of surfacing
as a StopIteration deep in the solver or a silently-skipped agent partway
through a live run against real providers.

Deliberately reuses load_survey_config/load_card for the checks they
already do (required fields, schema_version) rather than re-implementing
them; this module only adds the checks those loaders don't already make,
since they're meant to be forgiving enough to run, not to catch every
authoring mistake.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from .agent_card import load_card
from .config import ConfigError, load_survey_config
from .role_packs import get_role_pack_text

KNOWN_INSTRUMENTS = {"bwm", "ahp", "hierarchical_bwm"}


def _check_hierarchical_levels(levels: List[Dict[str, Any]]) -> List[str]:
    problems: List[str] = []
    if not levels:
        problems.append("hierarchical_bwm: instrument_params.levels is empty")
        return problems

    ids = [lvl.get("id") for lvl in levels]
    for lvl, lid in zip(levels, ids):
        if not lid:
            problems.append(f"hierarchical_bwm: a level is missing its 'id' field: {lvl}")
        if not lvl.get("dimensions"):
            problems.append(f"hierarchical_bwm: level '{lid}' has no (or empty) 'dimensions' list")

    roots = [lid for lvl, lid in zip(levels, ids) if not lvl.get("parent_level")]
    if len(roots) == 0:
        problems.append(
            "hierarchical_bwm: no level lacks a parent_level, so there is no root level; "
            "compute_global_weights() will crash with StopIteration on a real run"
        )
    elif len(roots) > 1:
        problems.append(f"hierarchical_bwm: more than one root level (no parent_level): {roots}")

    known_ids = set(ids)
    for lvl, lid in zip(levels, ids):
        parent_level = lvl.get("parent_level")
        if parent_level is None:
            continue
        if parent_level not in known_ids:
            problems.append(f"hierarchical_bwm: level '{lid}' has parent_level='{parent_level}', not a known level id")
            continue
        parent_lvl = next(p for p in levels if p.get("id") == parent_level)
        parent_criterion = lvl.get("parent_criterion")
        if not parent_criterion:
            problems.append(f"hierarchical_bwm: level '{lid}' has parent_level set but no parent_criterion")
        elif parent_criterion not in (parent_lvl.get("dimensions") or []):
            problems.append(
                f"hierarchical_bwm: level '{lid}'s parent_criterion='{parent_criterion}' is not among "
                f"parent level '{parent_level}'s dimensions {parent_lvl.get('dimensions')}"
            )
    return problems


def fix_survey(survey_dir: Path) -> List[str]:
    """Every problem found, as a plain human-readable string; an empty list
    means the survey looks structurally sound (not a guarantee every agent
    will produce a schema-valid response, only that the configuration
    itself is internally consistent)."""
    problems: List[str] = []

    try:
        survey = load_survey_config(survey_dir)
    except ConfigError as exc:
        return [f"survey.yaml: {exc}"]

    if survey.instrument not in KNOWN_INSTRUMENTS:
        problems.append(f"survey.yaml: unknown instrument '{survey.instrument}'. Known: {sorted(KNOWN_INSTRUMENTS)}")

    if survey.instrument == "hierarchical_bwm":
        levels = survey.instrument_params.get("levels", [])
        problems.extend(_check_hierarchical_levels(levels))
    elif not survey.instrument_params.get("dimensions"):
        problems.append(f"survey.yaml: instrument_params.dimensions is empty for instrument '{survey.instrument}'")

    for card_path in survey.agent_cards:
        try:
            card = load_card(card_path)
        except Exception as exc:  # noqa: BLE001 - report every load failure, never crash the whole check
            problems.append(f"{card_path.name}: failed to load agent card: {exc}")
            continue

        if card.instrument != survey.instrument:
            problems.append(
                f"{card_path.name}: card.instrument='{card.instrument}' does not match "
                f"survey.instrument='{survey.instrument}'"
            )

        if card.rag.enabled:
            if not card.rag.corpus_path:
                problems.append(f"{card_path.name}: rag.enabled=true but rag.corpus_path is unset")
            elif not Path(card.rag.corpus_path).is_dir():
                problems.append(
                    f"{card_path.name}: rag.corpus_path='{card.rag.corpus_path}' does not exist as a directory "
                    f"(relative to the current working directory)"
                )

        if card.role_pack and get_role_pack_text(card.role_pack) is None:
            problems.append(f"{card_path.name}: role_pack='{card.role_pack}' does not match any known role pack")

        if not card.system_prompt_override:
            template_path = Path(card.system_prompt_template)
            if not template_path.exists():
                problems.append(
                    f"{card_path.name}: system_prompt_template='{card.system_prompt_template}' does not exist "
                    f"relative to the current working directory"
                )

    return problems
