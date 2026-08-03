import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from symphysis.solvers import bwm_bayesian


def _synthetic_responses(n=8, seed=0):
    rng = np.random.default_rng(seed)
    codes = ["Q", "PT", "V", "IC", "L", "C"]
    responses = []
    for _ in range(n):
        best, worst = rng.choice(codes, size=2, replace=False)
        bto = {c: (1 if c == best else int(rng.integers(2, 9))) for c in codes}
        otw = {c: (1 if c == worst else int(rng.integers(2, 9))) for c in codes}
        responses.append({"best": best, "worst": worst, "best_to_others": bto, "others_to_worst": otw})
    return codes, responses


def test_bootstrap_produces_valid_posterior():
    codes, responses = _synthetic_responses()
    result = bwm_bayesian.solve_bootstrap(codes, responses, num_samples=500, random_seed=1)

    assert result.method == "numpy-bootstrap"
    assert abs(result.agg_mean.sum() - 1.0) < 1e-6
    assert np.all(result.agg_ci_lower <= result.agg_mean)
    assert np.all(result.agg_mean <= result.agg_ci_upper)
    assert result.credal_matrix.shape == (len(codes), len(codes))


@pytest.mark.slow
def test_pymc_prior_matches_reference_diffuse_gamma():
    """The concentration hyperprior must be the diffuse Gamma(0.01, 0.01) from
    the reference JAGS model (B2WME.txt), not the Gamma(1, 0.01) bug found and
    fixed in bsi-survey-app. This is a smoke test that the PyMC path runs and
    yields non-degenerate (non-zero-width) credible intervals; it does not
    re-derive the exact posterior."""
    if not bwm_bayesian.PYMC_AVAILABLE:
        pytest.skip("PyMC not installed")

    codes, responses = _synthetic_responses(n=10, seed=2)
    result = bwm_bayesian.solve_pymc(codes, responses, draws=300, tune=300, chains=2, progressbar=False)

    assert result.method == "pymc-nuts"
    ci_width = result.agg_ci_upper - result.agg_ci_lower
    assert np.all(ci_width > 1e-3), "credible intervals are suspiciously narrow; check the gamma prior"


def test_combine_panels_sweep_endpoints_match_each_panel():
    codes, human_resp = _synthetic_responses(n=5, seed=3)
    _, agent_resp = _synthetic_responses(n=5, seed=4)

    human = bwm_bayesian.solve_bootstrap(codes, human_resp, num_samples=300, random_seed=3)
    agent = bwm_bayesian.solve_bootstrap(codes, agent_resp, num_samples=300, random_seed=4)

    combined = bwm_bayesian.combine_panels(human, agent, alphas=[0.0, 0.6, 1.0])

    # alpha=1.0 -> pure human; alpha=0.0 -> pure agent (within resampling noise).
    assert np.allclose(combined[1.0].agg_mean, human.agg_mean, atol=0.05)
    assert np.allclose(combined[0.0].agg_mean, agent.agg_mean, atol=0.05)
