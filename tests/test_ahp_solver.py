import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from symphysis.solvers.ahp import aggregate_individual_priorities, solve_ahp

CODES = ["Q", "PT", "V"]


def test_solve_ahp_on_a_perfectly_consistent_matrix():
    # A = w_i / w_j exactly, for weights [0.6, 0.3, 0.1]: this matrix is
    # perfectly consistent (CR should be ~0) and lambda_max should equal n.
    w = np.array([0.6, 0.3, 0.1])
    matrix = [[w[i] / w[j] for j in range(3)] for i in range(3)]
    solution = solve_ahp(CODES, matrix)
    assert solution.consistent
    assert solution.consistency_ratio < 1e-6
    np.testing.assert_allclose(solution.weights, w, atol=1e-6)


def test_solve_ahp_weights_sum_to_one():
    matrix = [[1, 3, 5], [1 / 3, 1, 2], [1 / 5, 1 / 2, 1]]
    solution = solve_ahp(CODES, matrix)
    assert abs(sum(solution.weights) - 1.0) < 1e-9


def test_solve_ahp_flags_a_wildly_inconsistent_matrix():
    # Deliberately contradictory: Q > PT > V > Q in a strong cycle.
    matrix = [[1, 9, 1 / 9], [1 / 9, 1, 9], [9, 1 / 9, 1]]
    solution = solve_ahp(CODES, matrix)
    assert solution.consistency_ratio > 0.10
    assert not solution.consistent


def test_solve_ahp_rejects_wrong_shaped_matrix():
    import pytest

    with pytest.raises(ValueError):
        solve_ahp(CODES, [[1, 2], [0.5, 1]])


def test_aggregate_individual_priorities_geometric_mean():
    matrix_a = [[1, 2, 4], [0.5, 1, 2], [0.25, 0.5, 1]]
    matrix_b = [[1, 3, 5], [1 / 3, 1, 2], [1 / 5, 0.5, 1]]
    sol_a = solve_ahp(CODES, matrix_a)
    sol_b = solve_ahp(CODES, matrix_b)
    aggregated = aggregate_individual_priorities([sol_a, sol_b])
    assert abs(sum(aggregated) - 1.0) < 1e-9
    # Aggregated weight for each criterion should sit between the two
    # individual solutions' weights (geometric mean is a genuine average).
    for i in range(3):
        lo, hi = sorted([sol_a.weights[i], sol_b.weights[i]])
        assert lo - 1e-6 <= aggregated[i] <= hi + 1e-6
