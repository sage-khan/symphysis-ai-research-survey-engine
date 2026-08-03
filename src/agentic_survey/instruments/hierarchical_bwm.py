"""Hierarchical Best-Worst Method instrument: a survey defines several BWM
comparison sets ("levels"), each over its own subset of criteria, where one
level's criterion is itself elaborated by another, lower level (for example
TrustRouter's L1 criterion "DVS" is elaborated by six L2 trust dimensions,
one of which, "Q", is itself elaborated by three L3 quality clusters).

A flat instrument (bwm.py, ahp.py) cannot express this: it only knows one
set of criteria weighed once. This instrument asks an agent to complete
every level's BWM comparison in a single structured response, so the
existing one-call-per-sample Agent/guardrails/storage pipeline needs no
change; only the prompt is bigger and the parsed payload has one BWM
sub-answer per level instead of one flat answer.

instrument_params shape (see config.py's SurveyConfig for how this is
loaded from survey.yaml):

    composite_formula: "TrustRouter = DVS x F x (1 + E) x A"   # descriptive only
    levels:
      - id: "L1"
        name: "Top-level TrustRouter factors"
        description: "..."
        dimensions: ["DVS", "F", "E", "A"]
        dimension_labels: {"DVS": "Data Value Score", ...}
        dimension_descriptions: {"DVS": "Composite trustworthiness of the data.", ...}
      - id: "L2"
        name: "..."
        description: "..."
        dimensions: [...]
        dimension_labels: {...}
        parent_level: "L1"
        parent_criterion: "DVS"
      ...

`parent_level` / `parent_criterion` on a level record its place in the
hierarchy: this level's weights are the relative breakdown of that named
criterion in that named parent level. A level with no `parent_level` is a
root (there is normally exactly one, but nothing here assumes that).
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List

from .base import InstrumentResult
from ..qa_checks import extract_source_tags

_LEVEL_TASK_TEMPLATE = """\
### Level {level_id}: {level_name}
{level_description}

Criteria in this level:
{dimension_list}

Choose the single BEST (most important) and single WORST (least important) criterion in \
this level. Then, for every criterion j in this level (including Best itself), rate \
Best-to-Others (see the ratio rule above). Then, for every criterion j (including Worst \
itself), rate Others-to-Worst (see the ratio rule above).
"""

_INTRO_TEMPLATE = """\
You are completing a hierarchical Best-Worst Method (BWM) elicitation with {n_levels} \
separate comparison levels. {composite_note}Complete every level below independently: a \
criterion being "best" in one level says nothing about how it should be rated in a different \
level.

Ratio rule, applies to every level below: Best-to-Others and Others-to-Worst are RATIOS on a \
1-9 integer scale, not absolute importance scores. Best-to-itself is always exactly 1 (one \
time as more important as itself), never 9; the same applies to Worst-to-itself in \
Others-to-Worst. A rating of 9 for Best-to-Best would claim Best is nine times more important \
than itself, which is never correct. Worked example with placeholder criteria X, Y, Z (not \
any level's real criteria) where X is Best and Z is Worst: best_to_others = {{"X": 1, "Y": 4, \
"Z": 7}} (X vs itself is 1; X is rated 4x more important than Y and 7x more important than Z). \
others_to_worst = {{"X": 7, "Y": 3, "Z": 1}} (Z vs itself is 1; X is rated 7x more important \
than Z and Y is rated 3x more important than Z).

"""


def _pair_key_none():
    return None


class HierarchicalBWMInstrument:
    name = "hierarchical_bwm"

    def _levels(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        return params["levels"]

    def build_messages(
        self,
        agent_role_description: str,
        context_chunks: List[str],
        params: Dict[str, Any],
    ) -> List[Dict[str, str]]:
        levels = self._levels(params)
        composite = params.get("composite_formula")
        composite_note = f'The levels combine into the composite form "{composite}". ' if composite else ""

        sections = [_INTRO_TEMPLATE.format(n_levels=len(levels), composite_note=composite_note)]
        schema_lines = []
        for lvl in levels:
            codes = lvl["dimensions"]
            labels = lvl.get("dimension_labels", {})
            descriptions = lvl.get("dimension_descriptions", {})
            dim_lines = "\n".join(
                f"- {c}: {labels.get(c, c)}" + (f" ({descriptions[c]})" if descriptions.get(c) else "")
                for c in codes
            )
            sections.append(
                _LEVEL_TASK_TEMPLATE.format(
                    level_id=lvl["id"],
                    level_name=lvl.get("name", lvl["id"]),
                    level_description=lvl.get("description", ""),
                    dimension_list=dim_lines,
                )
            )
            example_pair = ", ".join(f'"{c}": <1-9 int>' for c in codes[:2]) + (", ..." if len(codes) > 2 else "")
            schema_lines.append(
                f'    "{lvl["id"]}": {{"best": "<code>", "worst": "<code>", '
                f'"best_to_others": {{{example_pair}}}, "others_to_worst": {{{example_pair}}}, '
                f'"reasoning": "<the actual logic for this level>"}}'
            )

        tags = extract_source_tags(context_chunks)
        real_tags = [t for t in tags if t != "general_knowledge"]
        if real_tags:
            tag_list = ", ".join(f'"{t}"' for t in real_tags)
            sources_instruction = (
                f'You were given reference material tagged with one or more of exactly these '
                f'labels: {tag_list}. List only the exact labels of material you genuinely drew '
                f'on across all levels. If you relied on your own background knowledge instead '
                f'of, or in addition to, that material, include "general_knowledge". Never list '
                f'a label for material you did not actually use.'
            )
        else:
            sources_instruction = 'You were not given any reference material for this task, so set "sources_used" to ["general_knowledge"].'

        joined_schema_lines = ",\n".join(schema_lines)
        sections.append(
            f"\n{sources_instruction}\n\n"
            "Respond with ONLY a JSON object, no other text, in exactly this shape, one entry "
            "per level:\n{\n"
            f'  "levels": {{\n{joined_schema_lines}\n  }},\n'
            '  "sources_used": ["<label>", ...]\n'
            "}"
        )

        task = "\n".join(sections)
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
        levels = self._levels(params)

        match = re.search(r"\{.*\}", raw_text, re.DOTALL)
        if not match:
            return InstrumentResult(valid=False, payload={}, errors=["No JSON object found in response"])
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            return InstrumentResult(valid=False, payload={}, errors=[f"JSON parse error: {exc}"])

        if "levels" not in data or not isinstance(data["levels"], dict):
            return InstrumentResult(valid=False, payload=data, errors=["Missing or malformed 'levels' object"])

        level_answers = data["levels"]
        for lvl in levels:
            lid = lvl["id"]
            codes = set(lvl["dimensions"])
            if lid not in level_answers:
                errors.append(f"Missing level '{lid}'")
                continue
            answer = level_answers[lid]
            if not isinstance(answer, dict):
                errors.append(f"Level '{lid}' answer must be an object")
                continue
            for key in ("best", "worst", "best_to_others", "others_to_worst"):
                if key not in answer:
                    errors.append(f"Level '{lid}' missing key '{key}'")
            if errors and any(e.startswith(f"Level '{lid}' missing") for e in errors):
                continue

            if answer["best"] not in codes:
                errors.append(f"Level '{lid}': best='{answer['best']}' is not a known code {sorted(codes)}")
            if answer["worst"] not in codes:
                errors.append(f"Level '{lid}': worst='{answer['worst']}' is not a known code {sorted(codes)}")
            if answer.get("best") == answer.get("worst"):
                errors.append(f"Level '{lid}': best and worst must differ")

            for field_name in ("best_to_others", "others_to_worst"):
                vec = answer.get(field_name, {})
                if not isinstance(vec, dict):
                    errors.append(f"Level '{lid}': {field_name} must be an object")
                    continue
                missing = codes - set(vec)
                if missing:
                    errors.append(f"Level '{lid}': {field_name} missing ratings for {sorted(missing)}")
                for code, value in vec.items():
                    if not isinstance(value, int) or isinstance(value, bool) or not (1 <= value <= 9):
                        errors.append(f"Level '{lid}': {field_name}[{code}]={value!r} is not an integer in 1-9")

            if not errors and answer.get("best") in codes:
                bto = answer["best_to_others"].get(answer["best"])
                if bto != 1:
                    errors.append(f"Level '{lid}': best_to_others[best] must be 1, got {bto}")
            if not errors and answer.get("worst") in codes:
                otw = answer["others_to_worst"].get(answer["worst"])
                if otw != 1:
                    errors.append(f"Level '{lid}': others_to_worst[worst] must be 1, got {otw}")

        if "sources_used" in data and not isinstance(data["sources_used"], list):
            errors.append(f"sources_used must be a list, got {type(data['sources_used']).__name__}")

        return InstrumentResult(valid=not errors, payload=data, errors=errors)
