"""Drives one full survey run: spawn agents, run the configured instrument,
solve the agent-panel posterior, optionally combine with a human panel
(HAWC-BWM), and write the report.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import integrity
from .agent import Agent
from .agent_card import AgentCard, AgentCardError, load_card
from .config import SurveyConfig
from .instruments.ahp import AHPInstrument, build_full_matrix
from .instruments.bwm import BWMInstrument
from .instruments.hierarchical_bwm import HierarchicalBWMInstrument
from .policy.authorization import PermissionError_
from .providers.base import ProviderError
from .reporting import (
    render_ahp_charts,
    render_ahp_report,
    render_charts,
    render_hierarchical_bwm_charts,
    render_hierarchical_bwm_report,
    render_methodology_section,
    render_per_agent_detail_section,
    render_report,
)
from .solvers import ahp as ahp_solver
from .solvers import bwm_bayesian, bwm_classical
from .solvers import hierarchical_bwm as hbwm_solver
from .audit.logger import SurveyStorage

# Every instrument this app can run a survey with. Adding a new method
# (Delphi, TOPSIS, and the rest of the candidates in README's Future
# Enhancements) means adding a new Instrument implementation plus a
# _solve_<name> function below and one new entry here; nothing else in
# this module, in Agent, or in storage needs to change to support it.
INSTRUMENTS = {"bwm": BWMInstrument(), "ahp": AHPInstrument(), "hierarchical_bwm": HierarchicalBWMInstrument()}


def _load_human_responses(path: Path) -> List[Dict[str, Any]]:
    """Generic per-expert JSON list: [{"expert_id", "best", "worst",
    "best_to_others", "others_to_worst"}, ...]. Any exporter (including a
    LimeSurvey export loader) can produce this shape."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON list of expert responses in {path}")
    return data


def _per_agent_entries(
    card: AgentCard, qa_status: Optional[bool], payload: Dict[str, Any]
) -> tuple[Dict[str, Any], Dict[str, Any]]:
    """One (per_agent_meta, per_agent_detail) pair for a single accepted
    sample payload. Factored out of the run_survey() loop so
    regenerate_report() can build the exact same shapes when replaying
    already-accepted samples from disk instead of freshly-run ones."""
    meta = {
        "agent_id": card.agent_id,
        "did": card.did.id,
        "role": card.role,
        "model": card.model.name,
        "provider": card.model.provider,
        "rag_enabled": card.rag.enabled,
    }
    answer = {k: v for k, v in payload.items() if k not in ("reasoning", "sources_used")}
    if "levels" in payload:
        # hierarchical_bwm's reasoning lives per level, not as one
        # top-level field; concatenate each level's own reasoning into one
        # readable block rather than showing "(no reasoning field
        # returned)" for a response that in fact gave a full, per-level
        # justification.
        reasoning = "\n\n".join(
            f"[{lid}] {lvl_answer.get('reasoning', '(no reasoning field returned)')}"
            for lid, lvl_answer in payload["levels"].items()
        )
    else:
        reasoning = payload.get("reasoning", "(no reasoning field returned)")
    detail = {
        "agent_id": card.agent_id,
        "display_name": card.display_name,
        "role": card.role,
        "model": f"{card.model.provider}/{card.model.name}",
        "did": card.did.id,
        "qa_precheck_passed": qa_status,
        "answer": answer,
        "reasoning": reasoning,
        "sources_used": payload.get("sources_used"),
    }
    return meta, detail


def _solve_and_write_report(
    survey: SurveyConfig,
    codes: List[str],
    storage: SurveyStorage,
    agent_payloads: List[Dict[str, Any]],
    per_agent_meta: List[Dict[str, Any]],
    per_agent_detail: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Solve the configured instrument over already-collected agent
    payloads and write the report/charts/combined_results/integrity
    manifest. Shared by run_survey() (payloads from a live agent panel run)
    and regenerate_report() (payloads replayed from each agent's own
    already-accepted samples/*.json on disk, so a hand-edited sample or a
    hand-edited rulefile that doesn't change any answer still gets
    reflected without re-running the whole survey against live providers)."""
    if survey.instrument == "ahp":
        result = _solve_ahp(survey, codes, agent_payloads, per_agent_meta)
        report_md = render_ahp_report(result)
        chart_paths = render_ahp_charts(result, storage.report_dir / "charts")
    elif survey.instrument == "hierarchical_bwm":
        result = _solve_hierarchical_bwm(survey, agent_payloads, per_agent_meta)
        report_md = render_hierarchical_bwm_report(result)
        chart_paths = render_hierarchical_bwm_charts(result, storage.report_dir / "charts")
    else:
        result = _solve_bwm(survey, codes, agent_payloads, per_agent_meta)
        report_md = render_report(result)
        chart_paths = render_charts(result, storage.report_dir / "charts")

    report_md += "\n\n" + render_methodology_section(survey.instrument, len(agent_payloads), chart_paths)
    report_md += "\n\n" + render_per_agent_detail_section(per_agent_detail)
    storage.write_report(report_md)

    storage.write_combined_results(result)
    # Written last, after every other output file exists: a SHA-256 of
    # everything the run actually produced, plus a plain SHA256SUMS file a
    # reviewer can check with nothing but sha256sum -c, no copy of this
    # app required. See integrity.py.
    integrity.write_manifest(survey.root)
    return result


def run_survey(survey: SurveyConfig) -> Dict[str, Any]:
    if survey.instrument not in INSTRUMENTS:
        raise ValueError(f"Unknown instrument '{survey.instrument}'. Known: {sorted(INSTRUMENTS)}")
    instrument = INSTRUMENTS[survey.instrument]
    storage = SurveyStorage(survey.root)

    # hierarchical_bwm has no single flat "dimensions" list (see
    # instruments/hierarchical_bwm.py's instrument_params shape); its
    # per-level dimensions are read directly from instrument_params by
    # _solve_hierarchical_bwm instead.
    codes: List[str] = survey.instrument_params.get("dimensions", [])

    agent_payloads: List[Dict[str, Any]] = []
    per_agent_meta: List[Dict[str, Any]] = []
    per_agent_detail: List[Dict[str, Any]] = []
    pending_notices: List[str] = []
    skipped_notices: List[str] = []
    for card_path in survey.agent_cards:
        card = load_card(card_path)
        try:
            agent = Agent(card, card_path, storage)
            run = agent.run(
                instrument,
                survey.instrument_params,
                survey_title=survey.title,
                survey_description=survey.description,
            )
        except (ProviderError, PermissionError_, AgentCardError) as exc:
            # A misconfigured or uncredentialed agent (missing API key,
            # permission violation, bad card) must not take down the whole
            # panel: skip it, log why, keep going. Distinct from a pending
            # manual response, which is expected and resolves on its own.
            skipped_notices.append(f"[{card.agent_id}] {type(exc).__name__}: {exc}")
            continue

        if run.pending_manual:
            pending_notices.append(f"[{card.agent_id}] {run.pending_manual}")

        # Loaded once per agent (not per sample): whether this agent's QA
        # precheck restatement matched its real configuration field for
        # field, or None if it has no precheck at all (a manual-provider
        # agent, which skips the automated precheck entirely).
        qa_status: Optional[bool] = None
        qa_path = storage.agent_dir(card.agent_id) / "qa_precheck.json"
        if qa_path.exists():
            qa_status = json.loads(qa_path.read_text(encoding="utf-8"))["verification"]["all_match"]

        for payload in [r.payload for r in run.accepted]:
            agent_payloads.append(payload)
            meta, detail = _per_agent_entries(card, qa_status, payload)
            per_agent_meta.append(meta)
            per_agent_detail.append(detail)

    if skipped_notices:
        print("Skipped agents (misconfigured or uncredentialed):")
        for notice in skipped_notices:
            print(f"  - {notice}")

    if pending_notices:
        print("Waiting on manually-pasted responses:")
        for notice in pending_notices:
            print(f"  - {notice}")

    if not agent_payloads:
        raise RuntimeError(
            "No agent produced a valid, schema-passing response; nothing to solve."
            + (" All configured agents are waiting on a manual paste; see notices above." if pending_notices else "")
            + (" Some agents were skipped; see notices above." if skipped_notices else "")
        )

    return _solve_and_write_report(survey, codes, storage, agent_payloads, per_agent_meta, per_agent_detail)


def regenerate_report(survey: SurveyConfig) -> Dict[str, Any]:
    """Re-solve and re-render the report/charts from each agent's own
    already-accepted samples/*.json on disk, without calling any provider
    or LLM. For an agent whose samples were hand-edited after the original
    run (correcting a malformed value, say), this picks up that edit; for
    every other agent it reproduces the exact same accepted payloads the
    original run already collected. Agents with no samples on disk (never
    run, or every sample was rejected) are skipped, exactly like a live
    run skips a misconfigured agent, and are reported the same way."""
    storage = SurveyStorage(survey.root)
    codes: List[str] = survey.instrument_params.get("dimensions", [])

    agent_payloads: List[Dict[str, Any]] = []
    per_agent_meta: List[Dict[str, Any]] = []
    per_agent_detail: List[Dict[str, Any]] = []
    skipped_notices: List[str] = []

    for card_path in survey.agent_cards:
        card = load_card(card_path)
        agent_dir = storage.agents_dir / card.agent_id
        samples_dir = agent_dir / "samples"
        sample_paths = sorted(samples_dir.glob("sample_*.json")) if samples_dir.exists() else []
        if not sample_paths:
            skipped_notices.append(f"[{card.agent_id}] no accepted samples found on disk to replay")
            continue

        qa_status: Optional[bool] = None
        qa_path = agent_dir / "qa_precheck.json"
        if qa_path.exists():
            qa_status = json.loads(qa_path.read_text(encoding="utf-8"))["verification"]["all_match"]

        for sample_path in sample_paths:
            payload = json.loads(sample_path.read_text(encoding="utf-8"))
            agent_payloads.append(payload)
            meta, detail = _per_agent_entries(card, qa_status, payload)
            per_agent_meta.append(meta)
            per_agent_detail.append(detail)

    if skipped_notices:
        print("Skipped agents (no accepted samples to replay):")
        for notice in skipped_notices:
            print(f"  - {notice}")

    if not agent_payloads:
        raise RuntimeError(
            "No agent has any accepted sample on disk to replay; nothing to solve. "
            "Run the survey at least once first (`symphysis run`)."
        )

    return _solve_and_write_report(survey, codes, storage, agent_payloads, per_agent_meta, per_agent_detail)


def _solve_bwm(
    survey: SurveyConfig, codes: List[str], agent_payloads: List[Dict[str, Any]], per_agent_meta: List[Dict[str, Any]]
) -> Dict[str, Any]:
    agent_classical = [
        bwm_classical.solve_bwm(codes, p["best"], p["worst"], p["best_to_others"], p["others_to_worst"])
        for p in agent_payloads
    ]
    agent_bayesian = bwm_bayesian.solve(codes, agent_payloads, method="auto")

    result: Dict[str, Any] = {
        "survey_id": survey.id,
        "title": survey.title,
        "dimensions": codes,
        "instrument": "bwm",
        "agent_panel": {
            "num_agents": len(agent_payloads),
            "per_agent_meta": per_agent_meta,
            "bayesian": _bayesian_to_dict(agent_bayesian),
            "classical_consistency": [
                {"consistent": c.consistent, "cr": c.consistency_ratio} for c in agent_classical
            ],
        },
    }

    human_path_str = survey.weighting.get("human_responses_path")
    if human_path_str:
        human_path = survey.root / human_path_str
        human_responses = _load_human_responses(human_path)
        human_bayesian = bwm_bayesian.solve(codes, human_responses, method="auto")
        alphas = survey.weighting.get("alpha_sweep", [0, 0.2, 0.4, 0.5, 0.6, 0.8, 1.0])
        headline_alpha = survey.weighting.get("headline_alpha", 0.6)

        combined = bwm_bayesian.combine_panels(human_bayesian, agent_bayesian, alphas)
        result["human_panel"] = {"num_experts": len(human_responses), "bayesian": _bayesian_to_dict(human_bayesian)}
        result["hawc_bwm"] = {
            "headline_alpha": headline_alpha,
            "sweep": {str(a): _bayesian_to_dict(r) for a, r in combined.items()},
        }

    return result


def _solve_ahp(
    survey: SurveyConfig, codes: List[str], agent_payloads: List[Dict[str, Any]], per_agent_meta: List[Dict[str, Any]]
) -> Dict[str, Any]:
    solutions = [
        ahp_solver.solve_ahp(codes, build_full_matrix(codes, p["comparisons"]))
        for p in agent_payloads
    ]
    aggregated = ahp_solver.aggregate_individual_priorities(solutions)

    individual_solutions = [
        {
            "agent_id": meta["agent_id"],
            "weights": {c: float(s.weights[i]) for i, c in enumerate(codes)},
            "lambda_max": s.lambda_max,
            "consistency_ratio": s.consistency_ratio,
            "consistent": s.consistent,
        }
        for meta, s in zip(per_agent_meta, solutions)
    ]

    return {
        "survey_id": survey.id,
        "title": survey.title,
        "dimensions": codes,
        "instrument": "ahp",
        "agent_panel": {
            "num_agents": len(agent_payloads),
            "per_agent_meta": per_agent_meta,
            "individual_solutions": individual_solutions,
            "aggregated_weights": {c: float(aggregated[i]) for i, c in enumerate(codes)},
        },
    }


def _solve_hierarchical_bwm(
    survey: SurveyConfig, agent_payloads: List[Dict[str, Any]], per_agent_meta: List[Dict[str, Any]]
) -> Dict[str, Any]:
    level_defs: List[Dict[str, Any]] = survey.instrument_params["levels"]

    level_solutions: Dict[str, hbwm_solver.LevelSolution] = {}
    levels_result: Dict[str, Any] = {}
    for lvl in level_defs:
        lid = lvl["id"]
        level_payloads = [p["levels"][lid] for p in agent_payloads]
        solution = hbwm_solver.solve_level(lvl["dimensions"], level_payloads)
        solution.level_id = lid
        level_solutions[lid] = solution
        levels_result[lid] = {
            "name": lvl.get("name", lid),
            "codes": solution.codes,
            "weights": solution.weights,
            "classical_consistency": solution.classical_consistency,
            "bayesian": solution.bayesian,
        }

    global_weights = hbwm_solver.compute_global_weights(level_defs, level_solutions)
    populated_equations = hbwm_solver.render_populated_equations(level_defs, level_solutions)

    return {
        "survey_id": survey.id,
        "title": survey.title,
        "dimensions": list(global_weights.keys()),
        "instrument": "hierarchical_bwm",
        "agent_panel": {
            "num_agents": len(agent_payloads),
            "per_agent_meta": per_agent_meta,
            "levels": levels_result,
            "global_weights": global_weights,
            "populated_equations": populated_equations,
            "composite_formula": survey.instrument_params.get("composite_formula"),
        },
    }


def _bayesian_to_dict(res: bwm_bayesian.BayesianResult) -> Dict[str, Any]:
    return {
        "criteria": res.criteria,
        "method": res.method,
        "num_experts": res.num_experts,
        "agg_mean": res.agg_mean.tolist(),
        "agg_ci_lower": res.agg_ci_lower.tolist(),
        "agg_ci_upper": res.agg_ci_upper.tolist(),
        "credal_matrix": res.credal_matrix.tolist(),
    }
