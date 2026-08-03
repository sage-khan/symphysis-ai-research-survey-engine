"""Classical Best-Worst Method (Rezaei, 2015), generic over any criteria set.

Ported and verified from VERITAS's bsi-survey-app (docs/research/Work-in-progress/
potential-papers/00-bsi/survey-app/src/survey_app/bwm.py), which was checked
line-by-line against Rezaei's published LP and consistency-index table; the
formulation here is unchanged. Only the interface is generalised from BSI's
fixed six-dimension schema to an arbitrary list of criterion codes, since this
app must serve future surveys/instruments, not just BSI.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

import numpy as np
from scipy.optimize import linprog

# Rezaei (2015) Table 1: maximum possible xi for each a_BW value.
CONSISTENCY_INDEX = {1: 0.00, 2: 0.44, 3: 1.00, 4: 1.63, 5: 2.30, 6: 3.00, 7: 3.73, 8: 4.47, 9: 5.23}
CR_THRESHOLD = 0.10


@dataclass
class BWMSolution:
    criteria: List[str]
    weights: np.ndarray
    xi_star: float
    consistency_ratio: float
    consistent: bool
    best: str
    worst: str
    best_to_others: Dict[str, int] = field(default_factory=dict)
    others_to_worst: Dict[str, int] = field(default_factory=dict)
    trace: List[str] = field(default_factory=list)


def solve_bwm(
    codes: List[str],
    best: str,
    worst: str,
    best_to_others: Dict[str, int],
    others_to_worst: Dict[str, int],
    cr_threshold: float = CR_THRESHOLD,
) -> BWMSolution:
    n = len(codes)
    best_idx = codes.index(best)
    worst_idx = codes.index(worst)

    A_B = np.array([best_to_others[c] for c in codes], dtype=float)
    A_W = np.array([others_to_worst[c] for c in codes], dtype=float)

    c = np.zeros(n + 1)
    c[-1] = 1.0

    A_ub: List[List[float]] = []
    b_ub: List[float] = []

    for j in range(n):
        if j == best_idx:
            continue
        row1 = [0.0] * (n + 1)
        row1[best_idx] = 1.0
        row1[j] = -A_B[j]
        row1[-1] = -1.0
        A_ub.append(row1)
        b_ub.append(0.0)
        row2 = [0.0] * (n + 1)
        row2[best_idx] = -1.0
        row2[j] = A_B[j]
        row2[-1] = -1.0
        A_ub.append(row2)
        b_ub.append(0.0)

    for j in range(n):
        if j == worst_idx:
            continue
        row1 = [0.0] * (n + 1)
        row1[j] = 1.0
        row1[worst_idx] = -A_W[j]
        row1[-1] = -1.0
        A_ub.append(row1)
        b_ub.append(0.0)
        row2 = [0.0] * (n + 1)
        row2[j] = -1.0
        row2[worst_idx] = A_W[j]
        row2[-1] = -1.0
        A_ub.append(row2)
        b_ub.append(0.0)

    A_eq = [[1.0] * n + [0.0]]
    b_eq = [1.0]
    bounds = [(0.0, None)] * (n + 1)

    result = linprog(c=c, A_ub=np.array(A_ub), b_ub=np.array(b_ub), A_eq=np.array(A_eq), b_eq=np.array(b_eq),
                      bounds=bounds, method="highs")
    if not result.success:
        raise RuntimeError(f"BWM LP failed: {result.message}")

    weights = result.x[:n]
    xi_star = float(result.x[n])
    a_bw = int(round(A_B[worst_idx]))
    ci = CONSISTENCY_INDEX.get(a_bw, CONSISTENCY_INDEX[9])
    cr = xi_star / ci if ci > 0 else 0.0

    trace = [
        f"Inputs: Best={best}, Worst={worst}",
        "Best-to-Others: " + ", ".join(f"{c}={int(A_B[j])}" for j, c in enumerate(codes)),
        "Others-to-Worst: " + ", ".join(f"{c}={int(A_W[j])}" for j, c in enumerate(codes)),
        "Optimal weights: " + ", ".join(f"{c}={weights[j]:.4f}" for j, c in enumerate(codes)),
        f"xi* = {xi_star:.4f}, a_BW={a_bw}, CI={ci:.2f}, CR={cr:.4f} "
        f"({'consistent' if cr <= cr_threshold else 'flag for review'})",
    ]

    return BWMSolution(
        criteria=codes, weights=weights, xi_star=xi_star, consistency_ratio=cr,
        consistent=cr <= cr_threshold, best=best, worst=worst,
        best_to_others=best_to_others, others_to_worst=others_to_worst, trace=trace,
    )
