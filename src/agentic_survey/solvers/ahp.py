"""Classical Analytic Hierarchy Process (Saaty, 1980), generic over any
criteria set. Priority weights via the principal eigenvector of the
pairwise comparison matrix; consistency ratio via Saaty's random index
table, the same formulation described in the original AHP method and
used unchanged across the standard AHP literature.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

import numpy as np

# Saaty (1980)'s random consistency index, by matrix order n=1..15.
RANDOM_INDEX = {
    1: 0.00, 2: 0.00, 3: 0.58, 4: 0.90, 5: 1.12, 6: 1.24, 7: 1.32, 8: 1.41,
    9: 1.45, 10: 1.49, 11: 1.51, 12: 1.48, 13: 1.56, 14: 1.57, 15: 1.59,
}
CR_THRESHOLD = 0.10


@dataclass
class AHPSolution:
    criteria: List[str]
    weights: np.ndarray
    lambda_max: float
    consistency_index: float
    consistency_ratio: float
    consistent: bool
    matrix: List[List[float]]
    trace: List[str] = field(default_factory=list)


def solve_ahp(codes: List[str], matrix: List[List[float]], cr_threshold: float = CR_THRESHOLD) -> AHPSolution:
    n = len(codes)
    A = np.array(matrix, dtype=float)
    if A.shape != (n, n):
        raise ValueError(f"Expected a {n}x{n} matrix, got {A.shape}")

    eigenvalues, eigenvectors = np.linalg.eig(A)
    # The principal eigenvalue of a positive reciprocal matrix is real,
    # positive, and the largest in magnitude (Perron-Frobenius); take its
    # real part defensively against floating-point noise in the
    # imaginary component.
    max_idx = int(np.argmax(eigenvalues.real))
    lambda_max = float(eigenvalues.real[max_idx])
    principal_vector = np.abs(eigenvectors[:, max_idx].real)
    weights = principal_vector / principal_vector.sum()

    ci = (lambda_max - n) / (n - 1) if n > 1 else 0.0
    ri = RANDOM_INDEX.get(n, RANDOM_INDEX[15])
    cr = ci / ri if ri > 0 else 0.0

    trace = [
        f"Pairwise comparison matrix over: {', '.join(codes)}",
        f"Principal eigenvalue (lambda_max) = {lambda_max:.4f}",
        "Priority weights: " + ", ".join(f"{c}={weights[j]:.4f}" for j, c in enumerate(codes)),
        f"CI = {ci:.4f}, RI(n={n}) = {ri:.2f}, CR = {cr:.4f} "
        f"({'consistent' if cr <= cr_threshold else 'flag for review, CR > 0.10'})",
    ]

    return AHPSolution(
        criteria=codes, weights=weights, lambda_max=lambda_max,
        consistency_index=ci, consistency_ratio=cr, consistent=cr <= cr_threshold,
        matrix=matrix, trace=trace,
    )


def aggregate_individual_priorities(solutions: List[AHPSolution]) -> np.ndarray:
    """Combine multiple agents' independently solved priority vectors into
    one group vector via the geometric mean (Aggregation of Individual
    Priorities, Forman and Peniwati 1998), renormalized to sum to 1. Using
    each agent's own already-solved weights, not re-solving a pooled
    matrix, keeps this consistent with how an individual agent's judgement
    is treated everywhere else in this app: as one complete, independent
    data point."""
    stacked = np.array([s.weights for s in solutions])
    geo_mean = np.exp(np.mean(np.log(stacked), axis=0))
    return geo_mean / geo_mean.sum()
