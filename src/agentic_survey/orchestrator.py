"""Drives one full survey run: spawn agents, run the configured instrument,
solve the agent-panel posterior, optionally combine with a human panel
(HAWC-BWM), and write the report.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .agent import Agent
from .config import SurveyConfig, load_agent_config
from .instruments.bwm import BWMInstrument
from .reporting import render_charts, render_report
from .solvers import bwm_bayesian, bwm_classical
from .storage import SurveyStorage

INSTRUMENTS = {"bwm": BWMInstrument()}


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
    for config_path in survey.agent_configs:
        agent_config = load_agent_config(config_path)
        agent = Agent(agent_config, storage)
        run = agent.run(instrument, survey.instrument_params)
        for payload in [r.payload for r in run.accepted]:
            agent_payloads.append(payload)
            per_agent_meta.append(
                {
                    "agent_id": agent_config.id,
                    "did": agent.did.did,
                    "role": agent_config.role,
                    "model": agent_config.model.name,
                    "provider": agent_config.model.provider,
                    "rag_enabled": agent_config.rag.enabled,
                }
            )

    if not agent_payloads:
        raise RuntimeError("No agent produced a valid, schema-passing response; nothing to solve.")

    agent_classical = [
        bwm_classical.solve_bwm(codes, p["best"], p["worst"], p["best_to_others"], p["others_to_worst"])
        for p in agent_payloads
    ]
    agent_bayesian = bwm_bayesian.solve(codes, agent_payloads, method="auto")

    result: Dict[str, Any] = {
        "survey_id": survey.id,
        "title": survey.title,
        "dimensions": codes,
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

    storage.write_combined_results(result)
    report_md = render_report(result)
    storage.write_report(report_md)
    render_charts(result, storage.report_dir / "charts")
    return result


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
