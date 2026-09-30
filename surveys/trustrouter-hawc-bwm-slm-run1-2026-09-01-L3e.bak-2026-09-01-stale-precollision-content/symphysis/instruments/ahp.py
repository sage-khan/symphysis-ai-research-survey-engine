"""Analytic Hierarchy Process instrument (Saaty, 1980).

Dimensions and labels come from the survey's instrument_params, exactly
like bwm.py; this module only knows the AHP response schema (an upper-
triangular pairwise comparison matrix on Saaty's 1-9 scale) and how to
validate it into a full reciprocal matrix.
"""

from __future__ import annotations

import json
import re
from itertools import combinations
from pathlib import Path
from typing import Any, Dict, List

from .base import InstrumentResult
from ..qa_checks import extract_source_tags

_DEFAULT_TASK_TEMPLATE = """\
You are completing an Analytic Hierarchy Process (AHP) pairwise comparison over the \
following criteria:
{dimension_list}

For every pair of criteria (i, j) listed below, state how many times more important i is \
than j, using Saaty's 1-9 scale:
1 = equally important, 3 = moderately more important, 5 = strongly more important, \
7 = very strongly more important, 9 = extremely more important (2, 4, 6, 8 are intermediate \
values). If j is actually more important than i, use the reciprocal instead: 1/3 = 0.333, \
1/5 = 0.2, 1/7 = 0.143, 1/9 = 0.111, and so on, as a decimal number, never a fraction string.

Pairs to rate:
{pair_list}

Step: state your reasoning honestly. Explain the actual logic behind your comparisons, in \
enough detail that a reviewer can follow why you rated each pair the way you did, not a \
generic restatement of the task.{sources_instruction}

Respond with ONLY a JSON object, no other text, in exactly this shape:
{{
  "comparisons": {{{comparison_schema_example}}},
  "reasoning": "<the actual logic behind your comparisons, for the audit log>",
  "sources_used": [{sources_schema_example}]
}}
"""

_SOURCES_INSTRUCTION_TEMPLATE = """ You were given reference material tagged with one or more \
of exactly these labels: {tag_list}. In "sources_used" below, list only the exact labels of \
material you genuinely drew on to reach your answer. If you relied on your own background \
knowledge instead of, or in addition to, that material, include "general_knowledge". Never \
list a label for material you did not actually use."""


def _pair_key(a: str, b: str) -> str:
    return f"{a}_vs_{b}"


class AHPInstrument:
    name = "ahp"

    def build_messages(
        self,
        agent_role_description: str,
        context_chunks: List[str],
        params: Dict[str, Any],
    ) -> List[Dict[str, str]]:
        codes: List[str] = params["dimensions"]
        labels: Dict[str, str] = params.get("dimension_labels", {})
        dimension_list = "\n".join(f"- {c}: {labels.get(c, c)}" for c in codes)
        pairs = list(combinations(codes, 2))
        pair_list = "\n".join(f"- {_pair_key(a, b)}" for a, b in pairs)
        comparison_schema_example = ", ".join(f'"{_pair_key(a, b)}": <number>' for a, b in pairs[:2]) + (", ..." if len(pairs) > 2 else "")

        tags = extract_source_tags(context_chunks)
        real_tags = [t for t in tags if t != "general_knowledge"]
        if real_tags:
            tag_list = ", ".join(f'"{t}"' for t in real_tags)
            sources_instruction = _SOURCES_INSTRUCTION_TEMPLATE.format(tag_list=tag_list)
        else:
            sources_instruction = (
                ' You were not given any reference material for this task, so set "sources_used" '
                'to ["general_knowledge"].'
            )

        task_template_path = params.get("task_template")
        template = Path(task_template_path).read_text(encoding="utf-8") if task_template_path else _DEFAULT_TASK_TEMPLATE
        task = template.format(
            dimension_list=dimension_list,
            pair_list=pair_list,
            comparison_schema_example=comparison_schema_example,
            sources_instruction=sources_instruction,
            sources_schema_example='"<label>", ...',
        )

        user_parts = [task]
        if context_chunks:
            joined = "\n\n---\n\n".join(context_chunks)
            user_parts.append(f"\nReference material to ground your judgement:\n\n{joined}")

        return [
            {"role": "system", "content": agent_role_description},
            {"role": "user", "content": "\n".join(user_parts)},
        ]

    def parse(self, raw_text: str, params: Dict[str, Any]) -> InstrumentResult:
        errors: List[str] = []
        codes: List[str] = params["dimensions"]
        expected_pairs = {_pair_key(a, b): (a, b) for a, b in combinations(codes, 2)}

        match = re.search(r"\{.*\}", raw_text, re.DOTALL)
        if not match:
            return InstrumentResult(valid=False, payload={}, errors=["No JSON object found in response"])

        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            return InstrumentResult(valid=False, payload={}, errors=[f"JSON parse error: {exc}"])

        if "comparisons" not in data:
            return InstrumentResult(valid=False, payload=data, errors=["Missing key 'comparisons'"])
        comparisons = data["comparisons"]
        if not isinstance(comparisons, dict):
            return InstrumentResult(valid=False, payload=data, errors=["'comparisons' must be an object"])

        missing = sorted(set(expected_pairs) - set(comparisons))
        if missing:
            errors.append(f"comparisons missing pairs: {missing}")
        for key, value in comparisons.items():
            if key not in expected_pairs:
                errors.append(f"comparisons has an unknown pair '{key}'")
                continue
            if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
                errors.append(f"comparisons['{key}']={value!r} must be a positive number")

        if "sources_used" in data and not isinstance(data["sources_used"], list):
            errors.append(f"sources_used must be a list, got {type(data['sources_used']).__name__}")

        return InstrumentResult(valid=not errors, payload=data, errors=errors)


def build_full_matrix(codes: List[str], comparisons: Dict[str, float]) -> List[List[float]]:
    """Expand a validated upper-triangular comparisons dict into the full
    n x n reciprocal matrix (diagonal 1, lower triangle = 1 / upper)."""
    n = len(codes)
    matrix = [[1.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            key = _pair_key(codes[i], codes[j])
            value = float(comparisons[key])
            matrix[i][j] = value
            matrix[j][i] = 1.0 / value
    return matrix
