"""Best-Worst Method instrument.

Dimensions, labels, and the task wording are all supplied by the survey's
instrument_params / an optional external template file, never hardcoded here;
this module only knows the BWM response schema (best, worst, best_to_others,
others_to_worst) and how to validate it.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List

from .base import InstrumentResult

_DEFAULT_TASK_TEMPLATE = """\
You are completing a Best-Worst Method (BWM) comparison over the following criteria:
{dimension_list}

Step 1: choose the single BEST (most important) and single WORST (least important) criterion.
Step 2: for every criterion j (including Best itself, which must be 1), rate how many times \
more important Best is than j, on a 1-9 integer scale (Best-to-Others).
Step 3: for every criterion j (including Worst itself, which must be 1), rate how many times \
more important j is than Worst, on a 1-9 integer scale (Others-to-Worst).

Respond with ONLY a JSON object, no other text, in exactly this shape:
{{
  "best": "<criterion code>",
  "worst": "<criterion code>",
  "best_to_others": {{"<code>": <1-9 int>, ...}},
  "others_to_worst": {{"<code>": <1-9 int>, ...}},
  "reasoning": "<1-3 sentences explaining the choice, for the audit log>"
}}
"""


class BWMInstrument:
    name = "bwm"

    def build_messages(
        self,
        agent_role_description: str,
        context_chunks: List[str],
        params: Dict[str, Any],
    ) -> List[Dict[str, str]]:
        codes: List[str] = params["dimensions"]
        labels: Dict[str, str] = params.get("dimension_labels", {})
        dimension_list = "\n".join(f"- {c}: {labels.get(c, c)}" for c in codes)

        task_template_path = params.get("task_template")
        template = Path(task_template_path).read_text(encoding="utf-8") if task_template_path else _DEFAULT_TASK_TEMPLATE
        task = template.format(dimension_list=dimension_list)

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
        codes = set(params["dimensions"])

        match = re.search(r"\{.*\}", raw_text, re.DOTALL)
        if not match:
            return InstrumentResult(valid=False, payload={}, errors=["No JSON object found in response"])

        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            return InstrumentResult(valid=False, payload={}, errors=[f"JSON parse error: {exc}"])

        for key in ("best", "worst", "best_to_others", "others_to_worst"):
            if key not in data:
                errors.append(f"Missing key '{key}'")
        if errors:
            return InstrumentResult(valid=False, payload=data, errors=errors)

        if data["best"] not in codes:
            errors.append(f"best='{data['best']}' is not a known criterion code {sorted(codes)}")
        if data["worst"] not in codes:
            errors.append(f"worst='{data['worst']}' is not a known criterion code {sorted(codes)}")
        if data.get("best") == data.get("worst"):
            errors.append("best and worst must differ")

        for field_name in ("best_to_others", "others_to_worst"):
            vec = data.get(field_name, {})
            missing = codes - set(vec)
            if missing:
                errors.append(f"{field_name} missing ratings for {sorted(missing)}")
            for code, value in vec.items():
                if not isinstance(value, int) or not (1 <= value <= 9):
                    errors.append(f"{field_name}[{code}]={value!r} is not an integer in 1-9")

        if not errors and data["best"] in codes:
            bto = data["best_to_others"].get(data["best"])
            if bto != 1:
                errors.append(f"best_to_others[best] must be 1, got {bto}")
        if not errors and data["worst"] in codes:
            otw = data["others_to_worst"].get(data["worst"])
            if otw != 1:
                errors.append(f"others_to_worst[worst] must be 1, got {otw}")

        return InstrumentResult(valid=not errors, payload=data, errors=errors)
