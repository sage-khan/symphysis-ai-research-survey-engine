"""Solves a hierarchical BWM survey (see instruments/hierarchical_bwm.py):
one classical + Bayesian BWM solve per level, then multiplies each level's
weights through its parent chain to compute global leaf weights and render
the fully populated composite equation, matching the structure and output
format of TrustRouter's own TRUSTROUTER_EQUATION.md (DVS = w1*Q + w2*PT +
..., L1 relative importance, global leaf weights).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from . import bwm_bayesian, bwm_classical


@dataclass
class LevelSolution:
    level_id: str
    codes: List[str]
    weights: Dict[str, float]              # this level's own (local) weights, sum to 1
    classical_consistency: List[Dict[str, Any]]  # per-agent {"consistent": bool, "cr": float}
    bayesian: Dict[str, Any]                # _bayesian_to_dict-shaped


def solve_level(codes: List[str], agent_payloads: List[Dict[str, Any]]) -> LevelSolution:
    """agent_payloads: this level's [{"best", "worst", "best_to_others",
    "others_to_worst"}, ...] across every agent that answered it."""
    classical = [
        bwm_classical.solve_bwm(codes, p["best"], p["worst"], p["best_to_others"], p["others_to_worst"])
        for p in agent_payloads
    ]
    bayesian = bwm_bayesian.solve(codes, agent_payloads, method="auto")
    weights = {c: float(bayesian.agg_mean[i]) for i, c in enumerate(codes)}
    return LevelSolution(
        level_id="",
        codes=codes,
        weights=weights,
        classical_consistency=[{"consistent": c.consistent, "cr": c.consistency_ratio} for c in classical],
        bayesian={
            "criteria": bayesian.criteria,
            "method": bayesian.method,
            "num_experts": bayesian.num_experts,
            "agg_mean": bayesian.agg_mean.tolist(),
            "agg_ci_lower": bayesian.agg_ci_lower.tolist(),
            "agg_ci_upper": bayesian.agg_ci_upper.tolist(),
        },
    )


def compute_global_weights(
    level_defs: List[Dict[str, Any]], level_solutions: Dict[str, LevelSolution]
) -> Dict[str, float]:
    """The weight of a leaf criterion within its own top-level branch's
    scope: its own level's local weight multiplied by every ancestor
    level's local weight for the criterion that level elaborates, EXCEPT
    the root level's own weight.

    The root is excluded deliberately, not by oversight: TrustRouter's
    real, published numbers (TRUSTROUTER_EQUATION.md) confirm this. L1's
    DVS/F/E/A weights express relative importance among factors combined
    multiplicatively at the very top (TrustRouter = DVS x F x (1+E) x A),
    not shares of one linear pie; multiplying a deeper leaf's weight by
    L1's own weight for its branch would conflate two different kinds of
    "importance" that do not compose linearly. A criterion that lives
    directly at the root (like F, which has no further breakdown) simply
    keeps its own root-level weight untouched, since there is nothing to
    multiply it by.

    A "leaf" here means any criterion that is not itself further broken
    down by a child level (for TrustRouter: F, IC, L, C, and every
    L3-level criterion).
    """
    root_id = next(lvl["id"] for lvl in level_defs if not lvl.get("parent_level"))
    parent_of_level = {lvl["id"]: (lvl.get("parent_level"), lvl.get("parent_criterion")) for lvl in level_defs}
    # A criterion is "elaborated" (not a leaf) if some level's parent_criterion points at it.
    elaborated: Dict[Any, str] = {}  # (parent_level, criterion) -> child_level_id
    for lvl in level_defs:
        pl, pc = lvl.get("parent_level"), lvl.get("parent_criterion")
        if pl and pc:
            elaborated[(pl, pc)] = lvl["id"]

    def _weight_below_root(level_id: str, code: str) -> float:
        """Local weight of `code` in `level_id`, times every ancestor's
        local weight, stopping before (not including) the root."""
        weight = level_solutions[level_id].weights[code]
        pl, pc = parent_of_level[level_id]
        if pl and pc and pl != root_id:
            weight *= _weight_below_root(pl, pc)
        return weight

    global_weights: Dict[str, float] = {}
    for lvl in level_defs:
        lid = lvl["id"]
        for code in lvl["dimensions"]:
            if (lid, code) in elaborated:
                continue  # not a leaf: its own children's global weights already cover it
            if lid == root_id:
                global_weights[code] = level_solutions[lid].weights[code]
            else:
                global_weights[code] = _weight_below_root(lid, code)
    return global_weights


def render_populated_equations(level_defs: List[Dict[str, Any]], level_solutions: Dict[str, LevelSolution]) -> List[str]:
    """One line per level whose criterion is itself named by another level
    (i.e. every level that is "inside" something), in the exact
    `Parent = w1*Child1 + w2*Child2 + ...` form TRUSTROUTER_EQUATION.md
    uses, using each level's own solved local weights."""
    lines = []
    for lvl in level_defs:
        pl, pc = lvl.get("parent_level"), lvl.get("parent_criterion")
        if not (pl and pc):
            continue
        sol = level_solutions[lvl["id"]]
        terms = " + ".join(f"{sol.weights[c]:.3f}*{c}" for c in lvl["dimensions"])
        lines.append(f"{pc} = {terms}")
    return lines
