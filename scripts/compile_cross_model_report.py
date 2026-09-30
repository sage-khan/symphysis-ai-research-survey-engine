"""Phase 5: parse every genuine (non-fabricated) TrustRouter panel condition's
per-level report.md, extract its Bayesian BWM weight table and consistency
count, and emit one consolidated cross-model markdown report.

Only conditions with real, verified provider-produced or genuinely-elicited
data are included -- see agentic-experiment-design-decisions.md (project-veritas)
for why the Gemini/ChatGPT manual-relay attempt (2026-09-04) is excluded:
those three files were produced by hardcoded Python heuristics, not any
actual model completion, and are never to be reported as real data.

Run:
    cd /path/to/symphysis-ai-research-survey-engine
    python3 scripts/compile_cross_model_report.py
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

CONDITIONS = [
    ("mistral:7b (agentic/OpenManus)", "trustrouter-agentic-full-panel-mistral-2026-09-01"),
    ("phi4:14b (agentic/OpenManus)", "trustrouter-agentic-full-panel-phi4-14b-2026-09-01"),
    ("llama3.1:8b (agentic/OpenManus)", "trustrouter-agentic-full-panel-llama3.1-8b-2026-09-01"),
    ("qwen3:14b (agentic/OpenManus)", "trustrouter-agentic-full-panel-qwen3-14b-2026-09-01"),
    ("qwen3:14b (direct completion)", "trustrouter-hawc-bwm-slm-run1-2026-09-01"),
    ("Claude Haiku (CLI)", "trustrouter-claude-cli-full-panel-claude-haiku-2026-09-01"),
    ("Claude Sonnet (CLI)", "trustrouter-claude-cli-full-panel-claude-sonnet-2026-09-01"),
]

LEVELS = [
    ("L1", "Top-level TrustRouter factors", ["DVS", "F", "E", "A"]),
    ("L2", "DVS constituents", ["Q", "PT", "V", "IC", "L", "C"]),
    ("L3a", "Quality (Q) sub-parts", ["IQ", "CQ", "RQ"]),
    ("L3b", "Provenance Trust (PT) sub-parts", ["T_source", "T_chain", "T_history"]),
    ("L3c", "Verification Strength (V) sub-parts", ["V_crypto", "V_audit", "V_diversity"]),
    ("L3d", "Attack Resistance (A) sub-parts", ["A_sybil", "A_oracle", "A_insider"]),
    ("L3e", "Economic Value (E) sub-parts", ["E_market", "E_liquidity", "E_demand"]),
]

ROW_RE = re.compile(r"^\|\s*([A-Za-z_]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*$", re.MULTILINE)
CONTRIB_RE = re.compile(r"Agents contributing a valid response:\s*(\d+)")
CONSIST_RE = re.compile(r"Classical BWM consistency:\s*(\d+)/(\d+) within threshold")


def parse_report(report_path: Path) -> dict | None:
    if not report_path.exists():
        return None
    text = report_path.read_text(encoding="utf-8")
    weights = {m.group(1): float(m.group(2)) for m in ROW_RE.finditer(text)}
    contrib_m = CONTRIB_RE.search(text)
    consist_m = CONSIST_RE.search(text)
    return {
        "weights": weights,
        "contributing": int(contrib_m.group(1)) if contrib_m else None,
        "consistent": (int(consist_m.group(1)), int(consist_m.group(2))) if consist_m else None,
    }


def main() -> None:
    data: dict[str, dict[str, dict]] = {}  # level_id -> condition_label -> parsed
    for label, prefix in CONDITIONS:
        for level_id, _, _ in LEVELS:
            survey_dir = REPO_ROOT / "surveys" / f"{prefix}-{level_id}"
            report_path = survey_dir / "report" / "report.md"
            parsed = parse_report(report_path)
            data.setdefault(level_id, {})[label] = parsed

    lines = [
        "# TrustRouter BWM Panel: Cross-Model Compilation Report",
        "",
        "Compiled 2026-09-04. Consolidates every genuinely-elicited condition of the TrustRouter",
        "Best-Worst Method expert panel across all 7 hierarchy levels: four locally-hosted SLMs run",
        "through the OpenManus agentic tool-calling harness (mistral:7b, phi4:14b, llama3.1:8b,",
        "qwen3:14b), qwen3:14b also run through the plain direct-completion path for an",
        "agentic-vs-direct comparison, and Claude Haiku and Claude Sonnet run through the Claude CLI",
        "provider. Each condition ran the full panel (6 construction-domain personas x base/RAG,",
        "3 independent repeats per agent) at every level.",
        "",
        "A parallel manual-relay attempt to add Gemini and ChatGPT web-UI conditions (2026-09-04)",
        "was abandoned and is excluded here: on inspection, the tool used to fill in the relay",
        "documents (Google Antigravity) had generated all responses from hardcoded Python lookup",
        "tables and heuristics rather than any actual model completion, confirmed directly from its",
        "own implementation plan and source. No data from that attempt appears anywhere below.",
        "",
        "**Note on sample counts:** the qwen3:14b direct-completion condition (`trustrouter-hawc-bwm-",
        "slm-run1`) is an earlier baseline run configured with `repeats=5` per agent, not 3. Its",
        "higher \"agents contributing\" counts (up to 60 rather than 36) reflect that deeper sampling,",
        "not a different agent panel or extra roles. Every other condition below used repeats=3.",
        "",
        "## How to read the tables",
        "",
        "Each level's table reports the Bayesian-solved mean weight per criterion (Mohammadi and",
        "Rezaei's hierarchical Bayesian BWM aggregation), one column per condition. **Bold** marks",
        "each condition's top-weighted criterion at that level. `n/a` means that condition/level",
        "combination has no report on disk (nothing was fabricated to fill the gap).",
        "",
    ]

    for level_id, level_name, criteria in LEVELS:
        lines.append(f"## {level_id}: {level_name}")
        lines.append("")
        header = "| Criterion | " + " | ".join(label for label, _ in CONDITIONS) + " |"
        sep = "|---|" + "---|" * len(CONDITIONS)
        lines.append(header)
        lines.append(sep)

        level_data = data[level_id]
        top_per_condition = {}
        for label, _ in CONDITIONS:
            parsed = level_data.get(label)
            if parsed and parsed["weights"]:
                top_per_condition[label] = max(parsed["weights"], key=parsed["weights"].get)

        for code in criteria:
            row = [code]
            for label, _ in CONDITIONS:
                parsed = level_data.get(label)
                if not parsed or code not in parsed["weights"]:
                    row.append("n/a")
                    continue
                val = parsed["weights"][code]
                cell = f"{val:.3f}"
                if top_per_condition.get(label) == code:
                    cell = f"**{cell}**"
                row.append(cell)
            lines.append("| " + " | ".join(row) + " |")
        lines.append("")

        # Consistency/contributing-agents footnote row
        meta_bits = []
        for label, _ in CONDITIONS:
            parsed = level_data.get(label)
            if not parsed:
                meta_bits.append(f"{label}: no report")
                continue
            c = parsed["contributing"]
            cons = parsed["consistent"]
            cons_str = f", {cons[0]}/{cons[1]} classically consistent" if cons else ""
            meta_bits.append(f"{label}: {c} agents contributing{cons_str}")
        lines.append("*" + "; ".join(meta_bits) + ".*")
        lines.append("")

        agreement = set(top_per_condition.values())
        if len(agreement) == 1:
            lines.append(f"**Cross-model agreement:** every condition ranks **{agreement.pop()}** highest at this level.")
        else:
            by_top = {}
            for label, top in top_per_condition.items():
                by_top.setdefault(top, []).append(label)
            agreement_str = "; ".join(f"{code} ({', '.join(labels)})" for code, labels in by_top.items())
            lines.append(f"**Cross-model divergence:** top-ranked criterion differs by condition: {agreement_str}.")
        lines.append("")

    lines.append("## Cross-level synthesis")
    lines.append("")
    lines.append(
        "Two levels show complete consensus: at L1 every condition ranks **DVS** (Data Value Score) "
        "as the dominant top-level factor, and at L3a every condition ranks **IQ** (Intrinsic Quality) "
        "highest within the Quality cluster. These are the two levels where the criteria differ most "
        "sharply in kind (a composite data-trust score versus mere feasibility/economics at L1; "
        "objective record correctness versus softer contextual quality at L3a), so the strong "
        "agreement suggests the panel converges most reliably when the comparison itself is least "
        "ambiguous."
    )
    lines.append("")
    lines.append(
        "The remaining five levels (L2, L3b, L3c, L3d, L3e) show a majority consensus with one or two "
        "consistent outliers rather than either unanimity or a genuine three-way split, with one "
        "exception: **L3b is the most divided level in the panel**, splitting three ways between "
        "T_source (the majority position), T_chain (Claude Haiku alone), and T_history (mistral:7b "
        "alone): the panel has no reliable consensus on what matters most for Provenance Trust."
    )
    lines.append("")
    lines.append(
        "**mistral:7b is the most frequent outlier**, diverging from the cross-model majority at both "
        "L3b (T_history over T_source) and L3d (A_sybil over A_insider, though only marginally: 0.397 "
        "vs. 0.393). Both are also mistral's two lowest classical-consistency runs (33/36 and 33/35), "
        "consistent with it being the smallest model in the panel (7B, versus 8-14B for the other "
        "local models and frontier scale for Claude). **Claude Haiku is the only frontier model to "
        "diverge from a strong majority**, breaking with every other condition at L2 (Q over C) and "
        "again at L3b (T_chain over T_source). Disagreement here is not simply a function of model "
        "size, since Haiku's divergence pattern does not track mistral's."
    )
    lines.append("")
    lines.append(
        "**Agentic versus direct completion (qwen3:14b, both conditions run on the identical model):** "
        "the two qwen3 conditions pick the same top-ranked criterion at every level without exception, "
        "and their weight magnitudes are close throughout (e.g. L1 DVS: 0.377 agentic vs. 0.381 direct; "
        "L3e E_demand: 0.433 vs. 0.446). The OpenManus agentic harness does not appear to change which "
        "criterion a model favors, at least for this model and this task. This is a useful negative "
        "result for anyone assuming tool-calling scaffolding would shift a model's expressed judgement."
    )
    lines.append("")

    out_path = REPO_ROOT.parent / "project-veritas" / "docs" / "research" / "Work-in-progress" / "potential-papers" / "00-trustrouter" / "symphysis-planning" / "trustrouter-cross-model-panel-report-2026-09-04.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
