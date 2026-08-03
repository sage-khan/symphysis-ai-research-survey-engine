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
from .agent_card import AgentCardError, load_card
from .config import SurveyConfig
from .instruments.ahp import AHPInstrument, build_full_matrix
from .instruments.bwm import BWMInstrument
from .permissions import PermissionError_
from .providers.base import ProviderError
from .reporting import render_ahp_charts, render_ahp_report, render_charts, render_report
from .solvers import ahp as ahp_solver
from .solvers import bwm_bayesian, bwm_classical
from .storage import SurveyStorage

# Every instrument this app can run a survey with. Adding a new method
# (Delphi, TOPSIS, and the rest of the candidates in README's Future
# Enhancements) means adding a new Instrument implementation plus a
# _solve_<name> function below and one new entry here; nothing else in
# this module, in Agent, or in storage needs to change to support it.
INSTRUMENTS = {"bwm": BWMInstrument(), "ahp": AHPInstrument()}


def _load_human_responses(path: Path) -> List[Dict[str, Any]]:
    """Generic per-expert JSON list: [{"expert_id", "best", "worst",
    "best_to_others", "others_to_worst"}, ...]. Any exporter (including the
    existing bsi-survey-app LimeSurvey loader) can produce this shape."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON list of expert responses in {path}")
    return data


def run_survey(survey: SurveyConfig) -> Dict[str, Any]:
    if survey.instrument not in INSTRUMENTS:
        raise ValueError(f"Unknown instrument '{survey.instrument}'. Known: {sorted(INSTRUMENTS)}")
    instrument = INSTRUMENTS[survey.instrument]
    storage = SurveyStorage(survey.root)

    codes: List[str] = survey.instrument_params["dimensions"]

    agent_payloads: List[Dict[str, Any]] = []
    per_agent_meta: List[Dict[str, Any]] = []
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
        for payload in [r.payload for r in run.accepted]:
            agent_payloads.append(payload)
            per_agent_meta.append(
                {
                    "agent_id": card.agent_id,
                    "did": card.did.id,
                    "role": card.role,
                    "model": card.model.name,
                    "provider": card.model.provider,
                    "rag_enabled": card.rag.enabled,
                }
            )

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

    if survey.instrument == "ahp":
        result = _solve_ahp(survey, codes, agent_payloads, per_agent_meta)
        report_md = render_ahp_report(result)
        storage.write_report(report_md)
        render_ahp_charts(result, storage.report_dir / "charts")
    else:
        result = _solve_bwm(survey, codes, agent_payloads, per_agent_meta)
        report_md = render_report(result)
        storage.write_report(report_md)
        render_charts(result, storage.report_dir / "charts")

    storage.write_combined_results(result)
    # Written last, after every other output file exists: a SHA-256 of
    # everything the run actually produced, plus a plain SHA256SUMS file a
    # reviewer can check with nothing but sha256sum -c, no copy of this
    # app required. See integrity.py.
    integrity.write_manifest(survey.root)
    return result


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
