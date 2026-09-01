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
from ..qa_checks import extract_source_tags

_DEFAULT_TASK_TEMPLATE = """\
You are completing a Best-Worst Method (BWM) comparison over the following criteria:
{dimension_list}

Step 1: choose the single BEST (most important) and single WORST (least important) criterion.
Step 2: for every criterion j (including Best itself), rate how many times more important \
Best is than j, on a 1-9 integer scale (Best-to-Others). This is a RATIO between Best and j, \
not an absolute importance score: Best compared to itself is always exactly 1 (one time as \
important as itself), never 9. A rating of 9 for Best-to-Best would claim Best is nine times \
more important than itself, which is never correct.
Step 3: for every criterion j (including Worst itself), rate how many times more important j \
is than Worst, on a 1-9 integer scale (Others-to-Worst). Worst compared to itself is always \
exactly 1, for the same reason.

Worked example with placeholder criteria X, Y, Z (not the real criteria above) where X is Best \
and Z is Worst: best_to_others = {{"X": 1, "Y": 4, "Z": 7}} (X vs itself is 1; X is rated 4x more \
important than Y and 7x more important than Z). others_to_worst = {{"X": 7, "Y": 3, "Z": 1}} (Z \
vs itself is 1; X is rated 7x more important than Z and Y is rated 3x more important than Z).

Step 4: state your reasoning honestly. Explain the actual logic behind your Best/Worst choice \
and your ratings, in enough detail that a reviewer can follow why you ranked the criteria this \
way, not a generic restatement of the task.{sources_instruction}

Respond with ONLY a JSON object, no other text, in exactly this shape:
{{
  "best": "<criterion code>",
  "worst": "<criterion code>",
  "best_to_others": {{"<code>": <1-9 int>, ...}},
  "others_to_worst": {{"<code>": <1-9 int>, ...}},
  "reasoning": "<the actual logic behind your choice, for the audit log>",
  "sources_used": [{sources_schema_example}]
}}
"""

_SOURCES_INSTRUCTION_TEMPLATE = """ You were given reference material tagged with one or more \
of exactly these labels: {tag_list}. In "sources_used" below, list only the exact labels of \
material you genuinely drew on to reach your answer. If you relied on your own background \
knowledge instead of, or in addition to, that material, include "general_knowledge". Never \
list a label for material you did not actually use."""


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
            sources_instruction=sources_instruction,
            sources_schema_example='"<label>", ...',
        )

        user_parts = [task]
        if context_chunks:
            joined = "\n\n---\n\n".join(context_chunks)
            user_parts.append(f"\nReference material to ground your judgement:\n\n{joined}")
            # Restated last, after the reference material: any reference material
            # (e.g. a verbatim human-facing survey instrument in the shared
            # knowledge repository, which correctly tells a HUMAN respondent to
            # write out full criterion labels) can otherwise be the last thing
            # read before generation and override the task's own short-code
            # requirement via simple recency, especially once RAG-retrieved
            # chunks make the reference material long. Found live: qwen3:14b
            # given RAG context reliably answered with full labels
            # ("DVS (Data Value Score)") instead of the bare code the JSON
            # schema requires, and in the worst cases abandoned JSON entirely
            # for prose, despite the schema appearing correctly earlier in the
            # same prompt. See docs/development/diagnostics.md.
            code_list = ", ".join(f'"{c}"' for c in codes)
            user_parts.append(
                "\nReminder, regardless of any wording used above in the reference material: "
                f"in your JSON answer, \"best\", \"worst\", and every key in \"best_to_others\"/"
                f"\"others_to_worst\" must be exactly one of these bare codes: {code_list} -- "
                "never the full label (e.g. \"DVS\", not \"DVS (Data Value Score)\" or "
                "\"Data Value Score\"). Respond with ONLY the JSON object, no other text."
            )

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
            if not isinstance(vec, dict):
                errors.append(f"{field_name} must be an object")
                continue
            missing = codes - set(vec)
            if missing:
                errors.append(f"{field_name} missing ratings for {sorted(missing)}")
            for code, value in vec.items():
                if not isinstance(value, int) or isinstance(value, bool) or not (1 <= value <= 9):
                    errors.append(f"{field_name}[{code}]={value!r} is not an integer in 1-9")

        if not errors and data["best"] in codes:
            bto = data["best_to_others"].get(data["best"])
            if bto != 1:
                errors.append(f"best_to_others[best] must be 1, got {bto}")
        if not errors and data["worst"] in codes:
            otw = data["others_to_worst"].get(data["worst"])
            if otw != 1:
                errors.append(f"others_to_worst[worst] must be 1, got {otw}")

        # sources_used is a soft genuineness signal (see qa_checks.verify_sources_used),
        # not a hard requirement: a model that omits it, or an external
        # task_template that predates this field, should not fail an
        # otherwise-valid Best/Worst response over it. Only reject if it is
        # present but the wrong type, since that is a real schema violation.
        if "sources_used" in data and not isinstance(data["sources_used"], list):
            errors.append(f"sources_used must be a list, got {type(data['sources_used']).__name__}")

        return InstrumentResult(valid=not errors, payload=data, errors=errors)
