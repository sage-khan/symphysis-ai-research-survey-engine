"""Bayesian Best-Worst Method (Mohammadi and Rezaei, 2020), generic over any
criteria set.

Ported from bsi-survey-app's implementation after verifying it against the
original author's reference JAGS model (github.com/Majeed7/BayesianBWM,
B2WME.txt). That comparison found one real deviation: the concentration
hyperprior was Gamma(1, 0.01) (mean 100) instead of the reference's diffuse
Gamma(0.01, 0.01) (mean ~1), which biases posteriors toward over-confident,
too-narrow credible intervals. Fixed here at the source before this became
the app's single BWM solver.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np

try:
    import pymc as pm
    import pytensor.tensor as pt
    PYMC_AVAILABLE = True
except Exception:  # pragma: no cover - import-time only
    PYMC_AVAILABLE = False


@dataclass
class BayesianResult:
    criteria: List[str]
    method: str
    num_experts: int
    num_samples: int
    agg_mean: np.ndarray
    agg_std: np.ndarray
    agg_ci_lower: np.ndarray
    agg_ci_upper: np.ndarray
    agg_samples: np.ndarray
    credal_matrix: np.ndarray
    concentration_mean: Optional[float] = None
    concentration_ci: Optional[tuple] = None


def _vectors(codes: List[str], responses: List[Dict]) -> tuple[np.ndarray, np.ndarray]:
    K, n = len(responses), len(codes)
    A_B = np.zeros((K, n))
    A_W = np.zeros((K, n))
    for k, r in enumerate(responses):
        for j, code in enumerate(codes):
            A_B[k, j] = float(r["best_to_others"][code])
            A_W[k, j] = float(r["others_to_worst"][code])
    return A_B, A_W


def _credal_matrix(agg_samples: np.ndarray) -> np.ndarray:
    S, n = agg_samples.shape
    credal = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            if i != j:
                credal[i, j] = np.mean(agg_samples[:, i] > agg_samples[:, j])
    return credal


def solve_pymc(
    codes: List[str],
    responses: List[Dict],
    draws: int = 1500,
    tune: int = 1000,
    chains: int = 2,
    target_accept: float = 0.95,
    random_seed: int = 42,
    progressbar: bool = False,
) -> BayesianResult:
    if not PYMC_AVAILABLE:
        raise RuntimeError("PyMC is not available. Install pymc or use solve_bootstrap.")

    A_B, A_W = _vectors(codes, responses)
    K, n = A_B.shape
    totals_B = A_B.sum(axis=1).astype(int)
    totals_W = A_W.sum(axis=1).astype(int)
    eps = 1e-6

    with pm.Model() as _:
        w_agg = pm.Dirichlet("w_agg", a=np.ones(n))
        # Gamma(0.01, 0.01): matches the reference JAGS model; see module docstring.
        gamma = pm.Gamma("gamma", alpha=0.01, beta=0.01)
        conc = gamma * w_agg + eps
        w_k = pm.Dirichlet("w_k", a=conc, shape=(K, n))

        inv_w = 1.0 / (w_k + eps)
        p_B = inv_w / pt.sum(inv_w, axis=1, keepdims=True)
        p_W = w_k

        pm.Multinomial("obs_B", n=totals_B, p=p_B, observed=A_B.astype(int))
        pm.Multinomial("obs_W", n=totals_W, p=p_W, observed=A_W.astype(int))

        trace = pm.sample(draws=draws, tune=tune, chains=chains, target_accept=target_accept,
                           random_seed=random_seed, progressbar=progressbar, compute_convergence_checks=False)

    agg_samples = trace.posterior["w_agg"].values.reshape(-1, n)
    gamma_samples = trace.posterior["gamma"].values.reshape(-1)

    return BayesianResult(
        criteria=codes, method="pymc-nuts", num_experts=K, num_samples=agg_samples.shape[0],
        agg_mean=agg_samples.mean(axis=0), agg_std=agg_samples.std(axis=0),
        agg_ci_lower=np.percentile(agg_samples, 2.5, axis=0),
        agg_ci_upper=np.percentile(agg_samples, 97.5, axis=0),
        agg_samples=agg_samples, credal_matrix=_credal_matrix(agg_samples),
        concentration_mean=float(gamma_samples.mean()),
        concentration_ci=(float(np.percentile(gamma_samples, 2.5)), float(np.percentile(gamma_samples, 97.5))),
    )


def _closed_form_weights(A_B_row: np.ndarray, A_W_row: np.ndarray) -> np.ndarray:
    inv_AB = 1.0 / np.maximum(A_B_row, 1e-6)
    w = inv_AB / inv_AB.sum()
    w2 = A_W_row / max(A_W_row.sum(), 1e-6)
    w = np.sqrt(w * w2)
    return w / w.sum()


def solve_bootstrap(codes: List[str], responses: List[Dict], num_samples: int = 2000, random_seed: int = 42) -> BayesianResult:
    rng = np.random.default_rng(random_seed)
    A_B, A_W = _vectors(codes, responses)
    K, n = A_B.shape

    expert_weights = np.array([_closed_form_weights(A_B[k], A_W[k]) for k in range(K)])
    agg_samples = np.zeros((num_samples, n))
    for s in range(num_samples):
        idx = rng.integers(0, K, size=K)
        sample = expert_weights[idx]
        log_w = np.log(np.clip(sample, 1e-12, None))
        w = np.exp(log_w.mean(axis=0))
        agg_samples[s] = w / w.sum()

    return BayesianResult(
        criteria=codes, method="numpy-bootstrap", num_experts=K, num_samples=num_samples,
        agg_mean=agg_samples.mean(axis=0), agg_std=agg_samples.std(axis=0),
        agg_ci_lower=np.percentile(agg_samples, 2.5, axis=0),
        agg_ci_upper=np.percentile(agg_samples, 97.5, axis=0),
        agg_samples=agg_samples, credal_matrix=_credal_matrix(agg_samples),
    )


def solve(codes: List[str], responses: List[Dict], method: str = "auto", **kwargs) -> BayesianResult:
    if method == "pymc":
        return solve_pymc(codes, responses, **kwargs)
    if method == "bootstrap":
        return solve_bootstrap(codes, responses, **kwargs)
    if method == "auto":
        if PYMC_AVAILABLE:
            try:
                return solve_pymc(codes, responses, **kwargs)
            except Exception:
                return solve_bootstrap(codes, responses, **kwargs)
        return solve_bootstrap(codes, responses, **kwargs)
    raise ValueError(f"Unknown method: {method}")


def combine_panels(
    human: BayesianResult,
    agent: BayesianResult,
    alphas: List[float],
) -> Dict[float, BayesianResult]:
    """HAWC-BWM draw-wise linear pool: w_combined = alpha*w_human + (1-alpha)*w_agent,
    for each alpha in `alphas` (e.g. the 0/0.2/0.4/0.5/0.6/0.8/1 sensitivity sweep).
    Sampled jointly (matched draw indices, resampled with replacement if the two
    panels have different sample counts) so uncertainty from both panels
    propagates into the combined credible interval rather than only the means.
    """
    if human.criteria != agent.criteria:
        raise ValueError("Human and agent panels must share the same criteria set")

    rng = np.random.default_rng(42)
    n_draws = max(human.agg_samples.shape[0], agent.agg_samples.shape[0])
    h_idx = rng.integers(0, human.agg_samples.shape[0], size=n_draws)
    a_idx = rng.integers(0, agent.agg_samples.shape[0], size=n_draws)
    h_samples = human.agg_samples[h_idx]
    a_samples = agent.agg_samples[a_idx]

    results: Dict[float, BayesianResult] = {}
    for alpha in alphas:
        combined_samples = alpha * h_samples + (1 - alpha) * a_samples
        results[alpha] = BayesianResult(
            criteria=human.criteria,
            method=f"hawc-bwm-alpha={alpha}",
            num_experts=human.num_experts + agent.num_experts,
            num_samples=n_draws,
            agg_mean=combined_samples.mean(axis=0),
            agg_std=combined_samples.std(axis=0),
            agg_ci_lower=np.percentile(combined_samples, 2.5, axis=0),
            agg_ci_upper=np.percentile(combined_samples, 97.5, axis=0),
            agg_samples=combined_samples,
            credal_matrix=_credal_matrix(combined_samples),
        )
    return results
