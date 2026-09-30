"""Validates hierarchical_bwm's hierarchy-multiplication math directly
against the real, published TrustRouter numbers in
docs/research/Work-in-progress/potential-papers/00-trustrouter/survey-app/
data/output/TRUSTROUTER_EQUATION.md, not just internally-consistent
synthetic numbers: this is the actual real-world structure this instrument
exists to compute correctly.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from symphysis.solvers.hierarchical_bwm import LevelSolution, compute_global_weights, render_populated_equations

# The real TrustRouter level structure (see trustrouter.py in the
# TrustRouter survey-app) and the real published local weights from
# TRUSTROUTER_EQUATION.md, reconstructed here as fixed LevelSolution
# objects (bypassing solve_level, since we are testing the hierarchy
# multiplication, not the BWM solver itself, which is already covered by
# test_bwm_bayesian.py and test_bwm_classical.py).
LEVEL_DEFS = [
    {"id": "L1", "dimensions": ["DVS", "F", "E", "A"]},
    {"id": "L2", "dimensions": ["Q", "PT", "V", "IC", "L", "C"], "parent_level": "L1", "parent_criterion": "DVS"},
    {"id": "L3a", "dimensions": ["IQ", "CQ", "RQ"], "parent_level": "L2", "parent_criterion": "Q"},
    {"id": "L3b", "dimensions": ["T_source", "T_chain", "T_history"], "parent_level": "L2", "parent_criterion": "PT"},
    {"id": "L3c", "dimensions": ["V_crypto", "V_audit", "V_diversity"], "parent_level": "L2", "parent_criterion": "V"},
    {"id": "L3d", "dimensions": ["A_sybil", "A_oracle", "A_insider"], "parent_level": "L1", "parent_criterion": "A"},
    {"id": "L3e", "dimensions": ["E_market", "E_liquidity", "E_demand"], "parent_level": "L1", "parent_criterion": "E"},
]


def _solution(level_id, codes, weights):
    return LevelSolution(level_id=level_id, codes=codes, weights=dict(zip(codes, weights)), classical_consistency=[], bayesian={})


def _real_trustrouter_solutions():
    return {
        "L1": _solution("L1", ["DVS", "F", "E", "A"], [0.309, 0.234, 0.205, 0.252]),
        "L2": _solution("L2", ["Q", "PT", "V", "IC", "L", "C"], [0.185, 0.169, 0.153, 0.147, 0.172, 0.175]),
        "L3a": _solution("L3a", ["IQ", "CQ", "RQ"], [0.333, 0.340, 0.327]),
        "L3b": _solution("L3b", ["T_source", "T_chain", "T_history"], [0.387, 0.308, 0.305]),
        "L3c": _solution("L3c", ["V_crypto", "V_audit", "V_diversity"], [0.307, 0.372, 0.321]),
        "L3d": _solution("L3d", ["A_sybil", "A_oracle", "A_insider"], [0.357, 0.373, 0.270]),
        "L3e": _solution("L3e", ["E_market", "E_liquidity", "E_demand"], [0.358, 0.296, 0.346]),
    }


def test_global_weights_match_the_real_published_trustrouter_numbers():
    solutions = _real_trustrouter_solutions()
    global_weights = compute_global_weights(LEVEL_DEFS, solutions)

    # From TRUSTROUTER_EQUATION.md's "Global leaf weights inside DVS" table.
    tol = 0.001
    assert global_weights["IQ"] == pytest.approx(0.0615, abs=tol)
    assert global_weights["CQ"] == pytest.approx(0.0629, abs=tol)
    assert global_weights["RQ"] == pytest.approx(0.0605, abs=tol)
    assert global_weights["T_source"] == pytest.approx(0.0654, abs=tol)
    assert global_weights["T_chain"] == pytest.approx(0.0520, abs=tol)
    assert global_weights["T_history"] == pytest.approx(0.0515, abs=tol)
    assert global_weights["V_crypto"] == pytest.approx(0.0470, abs=tol)
    assert global_weights["V_audit"] == pytest.approx(0.0569, abs=tol)
    assert global_weights["V_diversity"] == pytest.approx(0.0491, abs=tol)
    # Direct L2 leaves carry their L2 weight straight through, unscaled by
    # any child level (nothing elaborates them further).
    assert global_weights["IC"] == pytest.approx(0.147, abs=tol)
    assert global_weights["L"] == pytest.approx(0.172, abs=tol)
    assert global_weights["C"] == pytest.approx(0.175, abs=tol)
    # F is an L1 leaf with no child level at all.
    assert global_weights["F"] == pytest.approx(0.234, abs=tol)


def test_global_weights_cover_every_true_leaf_exactly_once():
    solutions = _real_trustrouter_solutions()
    global_weights = compute_global_weights(LEVEL_DEFS, solutions)
    expected_leaves = {
        "F", "IC", "L", "C",  # non-elaborated L1/L2 criteria
        "IQ", "CQ", "RQ", "T_source", "T_chain", "T_history",
        "V_crypto", "V_audit", "V_diversity",
        "A_sybil", "A_oracle", "A_insider",
        "E_market", "E_liquidity", "E_demand",
    }
    assert set(global_weights.keys()) == expected_leaves
    # DVS, Q, PT, V, E, A must NOT appear: each is fully accounted for by
    # its own children's global weights, so including it too would
    # double-count that share of the composite formula.
    for elaborated in ("DVS", "Q", "PT", "V", "E", "A"):
        assert elaborated not in global_weights


def test_render_populated_equations_matches_the_real_equation_shape():
    solutions = _real_trustrouter_solutions()
    lines = render_populated_equations(LEVEL_DEFS, solutions)
    assert any(line.startswith("DVS = ") for line in lines)
    assert any(line.startswith("Q = ") for line in lines)
    assert any(line.startswith("PT = ") for line in lines)
    assert any(line.startswith("V = ") for line in lines)
    assert any(line.startswith("A = ") for line in lines)
    assert any(line.startswith("E = ") for line in lines)
    # L1 itself is the root: nothing elaborates it, so it must not appear
    # on the left-hand side of a populated equation.
    assert not any(line.startswith("L1 = ") for line in lines)


def test_a_single_level_survey_with_no_hierarchy_is_all_leaves():
    flat_defs = [{"id": "L1", "dimensions": ["A", "B", "C"]}]
    solutions = {"L1": _solution("L1", ["A", "B", "C"], [0.5, 0.3, 0.2])}
    global_weights = compute_global_weights(flat_defs, solutions)
    assert global_weights == {"A": 0.5, "B": 0.3, "C": 0.2}
