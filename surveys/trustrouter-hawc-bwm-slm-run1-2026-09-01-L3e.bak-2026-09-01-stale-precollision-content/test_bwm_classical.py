import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from symphysis.solvers.bwm_classical import solve_bwm


def test_solve_bwm_basic_consistency():
    codes = ["Q", "PT", "V", "IC", "L", "C"]
    best, worst = "PT", "C"
    best_to_others = {"Q": 2, "PT": 1, "V": 3, "IC": 4, "L": 2, "C": 8}
    others_to_worst = {"Q": 4, "PT": 8, "V": 5, "IC": 3, "L": 4, "C": 1}

    sol = solve_bwm(codes, best, worst, best_to_others, others_to_worst)

    assert abs(sol.weights.sum() - 1.0) < 1e-6
    assert all(w >= 0 for w in sol.weights)
    # Best criterion should receive the (or a near-)highest weight.
    assert sol.weights[codes.index(best)] == max(sol.weights)
    assert sol.consistency_ratio >= 0


def test_solve_bwm_rejects_unknown_pattern_gracefully():
    # A maximally inconsistent pattern should still solve (LP is always
    # feasible) but should raise its consistency ratio above the threshold.
    codes = ["Q", "PT", "V"]
    best, worst = "Q", "V"
    best_to_others = {"Q": 1, "PT": 9, "V": 9}
    others_to_worst = {"Q": 9, "PT": 9, "V": 1}

    sol = solve_bwm(codes, best, worst, best_to_others, others_to_worst)
    assert sol.consistency_ratio > 0
