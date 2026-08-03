"""Markdown report generation, with matplotlib charts saved alongside it.

Chart generation is best-effort: if matplotlib is unavailable the markdown
report is still produced, just without embedded chart images.
"""

from __future__ import annotations

import json
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


_METHODOLOGY_TEXT = {
    "bwm": (
        "Each agent independently completed a Best-Worst Method (BWM) comparison: choosing the "
        "single most and least important criterion, then rating every criterion's importance "
        "relative to those two on a 1-9 scale. Individual responses were solved with the "
        "classical BWM linear program (Rezaei, 2015) for a consistency check, and combined "
        "across the panel with a hierarchical Bayesian model (Mohammadi and Rezaei, 2020)."
    ),
    "ahp": (
        "Each agent independently completed an Analytic Hierarchy Process (AHP) pairwise "
        "comparison over every pair of criteria, on Saaty's 1-9 scale (Saaty, 1980). Each "
        "agent's priority weights were solved via the principal eigenvector of their comparison "
        "matrix, with a consistency ratio computed against Saaty's random index; individual "
        "weight vectors were combined across the panel via geometric mean."
    ),
    "hierarchical_bwm": (
        "Each agent independently completed a separate Best-Worst Method comparison for every "
        "level of a multi-level hierarchy, where one level's criterion is itself broken down by "
        "another, lower level. Each level was solved independently (classical BWM for a "
        "consistency check per Rezaei 2015, Bayesian BWM per Mohammadi and Rezaei 2020 for the "
        "panel-level posterior), then every leaf criterion's global weight was computed by "
        "multiplying its own level's weight through every ancestor level's weight for the "
        "criterion it elaborates, all the way to the root of the composite formula."
    ),
}


def render_methodology_section(instrument: str, num_agents: int, chart_paths: "list[Path]") -> str:
    """A short, generated methodology paragraph plus the run's actual
    genuineness checks and embedded chart images, so a reader does not
    need this app's source to understand how the result was produced."""
    parts = ["## Methodology\n"]
    parts.append(
        _METHODOLOGY_TEXT.get(instrument, f"Each agent independently completed the '{instrument}' instrument.")
    )
    parts.append(f"\n\n{num_agents} agent response(s) were accepted into this result.\n")
    parts.append(
        "\nEvery agent's run began with a QA precheck (its stated configuration verified against "
        "ground truth) and every accepted answer's self-reported sources were checked against what "
        "reference material was actually available to it; see the Per-agent detail section below "
        "and this survey's Conversation Log for each agent's specific results. Every response is "
        "schema-validated and independently, repeatedly sampled (never a single completion treated "
        "as ground truth); see `guardrails.py`. This survey's complete output is covered by a "
        "SHA-256 integrity manifest (`integrity_manifest.json`, `SHA256SUMS`), generated once this "
        "run finished, so any later alteration to these files is detectable.\n"
    )
    if chart_paths:
        parts.append("\n### Charts\n")
        for path in chart_paths:
            name = Path(path).stem.replace("_", " ").title()
            parts.append(f"![{name}](charts/{Path(path).name})\n")
    return "\n".join(parts)


def render_per_agent_detail_section(per_agent_detail: "list[Dict[str, Any]]") -> str:
    """Every contributing agent's own answer, reasoning, cited sources, and
    QA precheck status, in full, for a reader who wants more than the
    aggregated numbers: exactly what each participant said and why."""
    parts = ["## Per-agent detail\n"]
    if not per_agent_detail:
        parts.append("_No agent contributed an accepted response._\n")
        return "\n".join(parts)

    for i, d in enumerate(per_agent_detail):
        display = d.get("display_name") or d["agent_id"]
        parts.append(f"### {display} (`{d['agent_id']}`)\n")
        parts.append(f"- Role: {d['role']}")
        parts.append(f"- Model: {d['model']}")
        parts.append(f"- DID: `{d['did']}`")
        qa = d["qa_precheck_passed"]
        qa_text = "passed" if qa is True else "FAILED, see Conversation Log" if qa is False else "not applicable (manual-provider agent)"
        parts.append(f"- QA precheck: {qa_text}")
        sources = d.get("sources_used")
        sources_text = ", ".join(sources) if isinstance(sources, list) else "(not reported)"
        parts.append(f"- Sources used: {sources_text}")
        parts.append(f"\n**Answer:** `{json.dumps(d['answer'])}`\n")
        parts.append(f"**Reasoning:**\n\n{d['reasoning']}\n")

    return "\n".join(parts)


def render_hierarchical_bwm_report(result: Dict[str, Any]) -> str:
    parts = [f"# Survey report: {result['title']}\n", f"Survey ID: `{result['survey_id']}`\n"]
    ap = result["agent_panel"]

    composite = ap.get("composite_formula")
    if composite:
        parts.append(f"**Composite form:** `{composite}`\n")

    parts.append(f"- Agents contributing a valid response: {ap['num_agents']}\n")

    for lid, lvl in ap["levels"].items():
        parts.append(f"## Level {lid}: {lvl['name']}\n")
        consistent = sum(1 for c in lvl["classical_consistency"] if c["consistent"])
        parts.append(f"- Classical BWM consistency: {consistent}/{len(lvl['classical_consistency'])} within threshold\n")
        b = lvl["bayesian"]
        parts.append(_weight_table(b["criteria"], b["agg_mean"], b["agg_ci_lower"], b["agg_ci_upper"]))
        parts.append("")

    parts.append("## Populated equations\n")
    for line in ap["populated_equations"]:
        parts.append(f"- `{line}`")
    parts.append("")

    parts.append("## Global leaf weights\n")
    parts.append("These are each leaf criterion's own level weight multiplied through every "
                 "ancestor level's weight for the criterion it elaborates, all the way to the root: "
                 "the actual coefficient each leaf carries in the fully expanded composite formula.\n")
    parts.append("| Criterion | Global weight |")
    parts.append("|---|---|")
    for code, weight in sorted(result["agent_panel"]["global_weights"].items(), key=lambda kv: -kv[1]):
        parts.append(f"| {code} | {weight:.4f} |")
    parts.append("")

    return "\n".join(parts)


def render_hierarchical_bwm_charts(result: Dict[str, Any], out_dir: Path) -> list[Path]:
    if not MATPLOTLIB_AVAILABLE:
        return []
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    ap = result["agent_panel"]

    for lid, lvl in ap["levels"].items():
        b = lvl["bayesian"]
        fig, ax = plt.subplots()
        ax.bar(b["criteria"], b["agg_mean"], yerr=[
            [max(0.0, m - l) for m, l in zip(b["agg_mean"], b["agg_ci_lower"])],
            [max(0.0, h - m) for m, h in zip(b["agg_mean"], b["agg_ci_upper"])],
        ], capsize=4)
        ax.set_ylabel("Weight")
        ax.set_title(f"Level {lid} posterior weights (95% CI)")
        path = out_dir / f"level_{lid}_weights.png"
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        written.append(path)

    global_weights = ap["global_weights"]
    codes = sorted(global_weights, key=lambda c: -global_weights[c])
    fig, ax = plt.subplots(figsize=(max(6, len(codes) * 0.6), 4))
    ax.bar(codes, [global_weights[c] for c in codes])
    ax.set_ylabel("Global weight")
    ax.set_title("Global leaf weights (fully expanded composite formula)")
    ax.tick_params(axis="x", rotation=60)
    path = out_dir / "global_leaf_weights.png"
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
