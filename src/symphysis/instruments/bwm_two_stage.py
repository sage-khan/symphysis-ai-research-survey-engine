"""Two-stage BWM elicitation: reasoning-model free text -> deterministic
parse, with no LLM-based "formatter" step in between.

Why this exists (see docs/research/.../00-trustrouter/symphysis-planning/
agentic-experiment-design-decisions.md, 2026-09-01 entries, in project-veritas
for the full experimental log): a single model both reasoning and calling a
submission tool in one turn proved fragile for mistral:7b (a system prompt
merely asking for reasoning-before-answering reliably broke native tool
calling). Splitting reasoning from structuring fixed that, but a second
LLM call to *format* the reasoning text into the schema introduced a new,
independently-measured failure mode: when the reasoning text's stated
labels do not map 1:1 onto the schema's expected keys, even a
function-calling-specialist model (xLAM-2-3b-fc-r) silently fabricates or
reshuffles values instead of recognizing the ambiguity — reliable in 5/5
trials when labels lined up exactly, unreliable in 4/5 when they did not.

This module removes that ambiguity at the source instead of trying to work
around it downstream: the reasoning stage is broken into two turns. Turn 1
elicits only best/worst (parsed deterministically). Turn 2's prompt is then
built DYNAMICALLY with the real factor names already substituted in --
never a generic "the other criteria" placeholder for the model to resolve
itself, since that placeholder-resolution step is exactly what a prior
version's system prompt got wrong 4 of 4 times (always restating the worst
factor's own name instead of the genuinely-remaining third factor). With no
placeholder for the model to misresolve, a plain regex parser can extract
the six explicit "<name> vs <name>: <int>" lines it was asked for, with a
missing or malformed line becoming a explicit parse failure -- never a
silently invented value.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass
class BestWorstResult:
    best: Optional[str]
    worst: Optional[str]
    errors: List[str]

    @property
    def valid(self) -> bool:
        return self.best is not None and self.worst is not None and not self.errors


@dataclass
class RatingsResult:
    ratings: Dict[Tuple[str, str], int]  # (from_code, to_code) -> 1-9
    errors: List[str]

    @property
    def valid(self) -> bool:
        return not self.errors


def build_best_worst_prompt(codes: List[str], labels: Dict[str, str]) -> str:
    dimension_list = "\n".join(f"- {c}: {labels.get(c, c)}" for c in codes)
    return (
        "You are comparing the following criteria:\n"
        f"{dimension_list}\n\n"
        "Which ONE criterion is BEST (most important), and which ONE is "
        "WORST (least important)? Answer in EXACTLY these two lines, using "
        f"the bare code only (one of {', '.join(codes)}), nothing else:\n"
        "Best factor: <code>\n"
        "Worst factor: <code>"
    )


_BEST_LINE_RE = re.compile(r"Best factor:\s*([A-Za-z0-9_]+)", re.IGNORECASE)
_WORST_LINE_RE = re.compile(r"Worst factor:\s*([A-Za-z0-9_]+)", re.IGNORECASE)


def parse_best_worst(text: str, codes: List[str]) -> BestWorstResult:
    errors: List[str] = []
    code_set = set(codes)

    best_match = _BEST_LINE_RE.search(text)
    worst_match = _WORST_LINE_RE.search(text)

    best = best_match.group(1) if best_match else None
    worst = worst_match.group(1) if worst_match else None

    if best is None:
        errors.append("No 'Best factor: <code>' line found")
    elif best not in code_set:
        errors.append(f"best={best!r} is not a known code {sorted(code_set)}")
        best = None

    if worst is None:
        errors.append("No 'Worst factor: <code>' line found")
    elif worst not in code_set:
        errors.append(f"worst={worst!r} is not a known code {sorted(code_set)}")
        worst = None

    if best is not None and worst is not None and best == worst:
        errors.append("best and worst must differ")
        best = worst = None

    return BestWorstResult(best=best, worst=worst, errors=errors)


def build_ratings_prompt(
    best: str, worst: str, others: List[str], labels: Dict[str, str]
) -> str:
    """others = the codes that are neither best nor worst (exactly n-2 of
    them). Every line below names real codes already known at prompt-build
    time -- nothing is left for the model to resolve on its own."""
    lines = [f"You said the BEST factor is {best} ({labels.get(best, best)}) "
             f"and the WORST factor is {worst} ({labels.get(worst, worst)})."]
    lines.append(
        "Now state exactly the following ratings, each on a 1-9 integer "
        "scale (1 = equally important, 9 = extremely more important), "
        "one per line, in EXACTLY this format (replace only <N>):"
    )
    pairs: List[Tuple[str, str]] = []
    for o in others:
        pairs.append((best, o))
    pairs.append((best, worst))
    for o in others:
        pairs.append((o, worst))
    for a, b in pairs:
        lines.append(f"{a} vs {b}: <N>")
    return "\n".join(lines)


def _pair_regex(a: str, b: str) -> re.Pattern:
    return re.compile(
        rf"\b{re.escape(a)}\s+vs\.?\s+{re.escape(b)}\s*:\s*(\d+)", re.IGNORECASE
    )


def parse_ratings(
    text: str, best: str, worst: str, others: List[str]
) -> RatingsResult:
    errors: List[str] = []
    ratings: Dict[Tuple[str, str], int] = {}

    pairs: List[Tuple[str, str]] = [(best, o) for o in others]
    pairs.append((best, worst))
    pairs.extend((o, worst) for o in others)

    for a, b in pairs:
        match = _pair_regex(a, b).search(text)
        if match is None:
            errors.append(f"No explicit '{a} vs {b}: <N>' line found")
            continue
        value = int(match.group(1))
        if not (1 <= value <= 9):
            errors.append(f"{a} vs {b} = {value} is out of the required 1-9 range")
            continue
        ratings[(a, b)] = value

    return RatingsResult(ratings=ratings, errors=errors)


def assemble_bwm_payload(
    codes: List[str],
    best: str,
    worst: str,
    ratings: Dict[Tuple[str, str], int],
    reasoning_text: str,
) -> Dict:
    """Builds the exact payload shape instruments/bwm.py::BWMInstrument.parse()
    validates: best, worst, best_to_others (all `codes`, self=1),
    others_to_worst (all `codes`, self=1), reasoning. Raises KeyError if a
    required (a, b) pair is missing from `ratings` -- callers must check
    RatingsResult.valid before calling this, never assemble a partial
    payload silently."""
    others = [c for c in codes if c not in (best, worst)]

    best_to_others = {best: 1}
    for o in others:
        best_to_others[o] = ratings[(best, o)]
    best_to_others[worst] = ratings[(best, worst)]

    others_to_worst = {worst: 1}
    for o in others:
        others_to_worst[o] = ratings[(o, worst)]
    others_to_worst[best] = ratings[(best, worst)]

    return {
        "best": best,
        "worst": worst,
        "best_to_others": best_to_others,
        "others_to_worst": others_to_worst,
        "reasoning": reasoning_text,
    }
