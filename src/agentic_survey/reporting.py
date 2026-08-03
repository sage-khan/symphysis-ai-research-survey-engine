"""Markdown report generation, with matplotlib charts saved alongside it.

Chart generation is best-effort: if matplotlib is unavailable the markdown
report is still produced, just without embedded chart images.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:  # pragma: no cover - import-time only
    MATPLOTLIB_AVAILABLE = False


def _weight_table(criteria, mean, lo, hi) -> str:
    lines = ["| Criterion | Mean | 95% CI lower | 95% CI upper |", "|---|---|---|---|"]
    for c, m, l, h in zip(criteria, mean, lo, hi):
        lines.append(f"| {c} | {m:.4f} | {l:.4f} | {h:.4f} |")
    return "\n".join(lines)


def render_report(result: Dict[str, Any]) -> str:
    parts = [f"# Survey report: {result['title']}\n", f"Survey ID: `{result['survey_id']}`\n"]

    ap = result["agent_panel"]
    parts.append("## Agent panel\n")
    parts.append(f"- Agents contributing a valid response: {ap['num_agents']}")
    consistent = sum(1 for c in ap["classical_consistency"] if c["consistent"])
    parts.append(f"- Classical BWM consistency: {consistent}/{len(ap['classical_consistency'])} within threshold\n")
    b = ap["bayesian"]
    parts.append(_weight_table(b["criteria"], b["agg_mean"], b["agg_ci_lower"], b["agg_ci_upper"]))
    parts.append("")

    if "human_panel" in result:
        hp = result["human_panel"]
        parts.append("## Human panel\n")
        parts.append(f"- Experts: {hp['num_experts']}\n")
        hb = hp["bayesian"]
        parts.append(_weight_table(hb["criteria"], hb["agg_mean"], hb["agg_ci_lower"], hb["agg_ci_upper"]))
        parts.append("")

        hw = result["hawc_bwm"]
        parts.append("## HAWC-BWM combined panel\n")
        parts.append(f"Headline weighting: alpha = {hw['headline_alpha']} (human weight)\n")
        headline = hw["sweep"].get(str(hw["headline_alpha"]))
        if headline:
            parts.append("### Headline combined weights\n")
            parts.append(_weight_table(headline["criteria"], headline["agg_mean"], headline["agg_ci_lower"], headline["agg_ci_upper"]))
            parts.append("")

        parts.append("### Full sensitivity sweep\n")
        parts.append("| alpha (human weight) | " + " | ".join(hw["sweep"][next(iter(hw["sweep"]))]["criteria"]) + " |")
        parts.append("|---|" + "---|" * len(hw["sweep"][next(iter(hw["sweep"]))]["criteria"]))
        for alpha_str, res in hw["sweep"].items():
            row = " | ".join(f"{m:.4f}" for m in res["agg_mean"])
            parts.append(f"| {alpha_str} | {row} |")
        parts.append("")

    return "\n".join(parts)


def render_ahp_report(result: Dict[str, Any]) -> str:
    parts = [f"# Survey report: {result['title']}\n", f"Survey ID: `{result['survey_id']}`\n"]
    ap = result["agent_panel"]
    parts.append("## Agent panel (Analytic Hierarchy Process)\n")
    parts.append(f"- Agents contributing a valid response: {ap['num_agents']}")
    consistent = sum(1 for s in ap["individual_solutions"] if s["consistent"])
    parts.append(f"- Individual consistency ratio within Saaty's 0.10 threshold: {consistent}/{len(ap['individual_solutions'])}\n")

    parts.append("### Aggregated priority weights (geometric mean across agents)\n")
    parts.append("| Criterion | Aggregated weight |")
    parts.append("|---|---|")
    for code in result["dimensions"]:
        parts.append(f"| {code} | {ap['aggregated_weights'][code]:.4f} |")
    parts.append("")

    parts.append("### Per-agent solutions\n")
    parts.append("| Agent | Consistency ratio | Consistent | " + " | ".join(result["dimensions"]) + " |")
    parts.append("|---|---|---|" + "---|" * len(result["dimensions"]))
    for s in ap["individual_solutions"]:
        weights_row = " | ".join(f"{s['weights'][c]:.4f}" for c in result["dimensions"])
        parts.append(f"| {s['agent_id']} | {s['consistency_ratio']:.4f} | {'yes' if s['consistent'] else 'FLAG'} | {weights_row} |")
    parts.append("")

    return "\n".join(parts)


def render_ahp_charts(result: Dict[str, Any], out_dir: Path) -> list[Path]:
    if not MATPLOTLIB_AVAILABLE:
        return []
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    ap = result["agent_panel"]
    criteria = result["dimensions"]
    aggregated = [ap["aggregated_weights"][c] for c in criteria]
    fig, ax = plt.subplots()
    ax.bar(criteria, aggregated)
    ax.set_ylabel("Aggregated priority weight")
    ax.set_title("AHP aggregated priority weights (geometric mean across agents)")
    path = out_dir / "ahp_aggregated_weights.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    written.append(path)

    return written


def render_charts(result: Dict[str, Any], out_dir: Path) -> list[Path]:
    if not MATPLOTLIB_AVAILABLE:
        return []
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    ap = result["agent_panel"]["bayesian"]
    fig, ax = plt.subplots()
    ax.bar(ap["criteria"], ap["agg_mean"], yerr=[
        # Clipped at 0: with very few samples (e.g. a single-agent panel,
        # or a criterion whose bootstrap draws all collapse to the same
        # value) floating-point rounding in the mean/percentile can put the
        # CI bound a sliver on the wrong side of the mean, and matplotlib
        # hard-rejects a negative yerr rather than treating it as ~0.
        [max(0.0, m - l) for m, l in zip(ap["agg_mean"], ap["agg_ci_lower"])],
        [max(0.0, h - m) for m, h in zip(ap["agg_mean"], ap["agg_ci_upper"])],
    ], capsize=4)
    ax.set_ylabel("Weight")
    ax.set_title("Agent panel posterior weights (95% CI)")
    path = out_dir / "agent_panel_weights.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    written.append(path)

    if "hawc_bwm" in result:
        sweep = result["hawc_bwm"]["sweep"]
        criteria = sweep[next(iter(sweep))]["criteria"]
        alphas = sorted(sweep.keys(), key=float)
        fig, ax = plt.subplots()
        for i, crit in enumerate(criteria):
            ax.plot(
                [float(a) for a in alphas],
                [sweep[a]["agg_mean"][i] for a in alphas],
                marker="o",
                label=crit,
            )
        ax.set_xlabel("alpha (human weight)")
        ax.set_ylabel("Combined weight")
        ax.set_title("HAWC-BWM sensitivity sweep")
        ax.legend(fontsize="small")
        path = out_dir / "hawc_bwm_sensitivity_sweep.png"
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        written.append(path)

    return written
