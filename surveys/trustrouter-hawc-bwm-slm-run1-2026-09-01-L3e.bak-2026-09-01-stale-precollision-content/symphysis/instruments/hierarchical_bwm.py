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
this level. Then, for every criterion j in this level, rate Best-to-Others: a ratio, not an \
importance score, so Best-to-itself is exactly 1, never 9 (see the ratio rule above for why). \
Then, for every criterion j, rate Others-to-Worst: Worst-to-itself is exactly 1, never 9, for \
the same reason.
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

_PANEL_LEVEL_INSTRUCTION_TEMPLATE = """\
Ratio rule for this level: Best-to-Others and Others-to-Worst are RATIOS on a 1-9 integer \
scale, not absolute importance scores. Best-to-itself is always exactly 1, never 9; the same \
applies to Worst-to-itself in Others-to-Worst.

Once you have your answer, call the instrument_submit tool with exactly these arguments: \
level_id="{level_id}", best="<code>", worst="<code>", \
best_to_others={{{full_pair}}}, others_to_worst={{{full_pair}}}, reasoning="<your reasoning>". \
Every criterion code listed above MUST appear as a key in both best_to_others and \
others_to_worst, including the best and worst criteria themselves (rated 1 against themselves, \
per the ratio rule above). If instrument_submit reports errors, fix exactly those problems and \
call it again with a corrected submission. Once it reports valid=true, call the terminate tool \
to finish this level.
"""


def _pair_key_none():
    return None


class HierarchicalBWMInstrument:
    name = "hierarchical_bwm"

    def _levels(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        return params["levels"]

    def levels_for_panel(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Public entry point signaling this instrument supports per-level
        panel submission (see runtime/openmanus.py's "survey_panel" flow,
        docs/architecture/governance-layer-and-runtime-backends-plan.md
        Phase 3): a flat instrument (bwm.py, ahp.py) has no levels() and
        does not implement this method at all, so Agent.run() duck-types
        on hasattr(instrument, "levels_for_panel") to decide whether panel
        mode is even applicable, rather than instrument type-checking."""
        return self._levels(params)

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
            full_pair = ", ".join(f'"{c}": <1-9 int>' for c in codes)
            schema_lines.append(
                f'    "{lvl["id"]}": {{"best": "<code>", "worst": "<code>", '
                f'"best_to_others": {{{full_pair}}}, "others_to_worst": {{{full_pair}}}, '
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
            "per level. Every criterion code listed for a level below MUST appear as a key in "
            "both that level's best_to_others and others_to_worst objects, including the best "
            "and worst criteria themselves (rated 1 against themselves, per the ratio rule "
            "above): a level with 6 criteria needs 6 keys in each object, never fewer:\n{\n"
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

    def build_level_messages(
        self,
        level_id: str,
        agent_role_description: str,
        context_chunks: List[str],
        params: Dict[str, Any],
    ) -> List[Dict[str, str]]:
        """Per-level counterpart to build_messages(), used only by the
        "survey_panel" OpenManus flow (Phase 3): one level's task
        description plus an explicit instruction to submit via the
        instrument_submit tool rather than emit JSON directly, since a
        ToolCallAgent step loop drives this instead of a single free-text
        completion.

        Deliberately does not carry sources_used into panel mode: that
        field tracks which reference material was used across an ENTIRE
        response, not one level, and parse()'s outer validation already
        treats it as optional, so omitting it here changes nothing about
        correctness, only avoids asking a whole-response question once per
        level. If per-level source attribution becomes a real requirement,
        extend this prompt and the instrument_submit schema together, in
        one change, not piecemeal."""
        levels_by_id = {lvl["id"]: lvl for lvl in self._levels(params)}
        lvl = levels_by_id[level_id]
        codes = lvl["dimensions"]
        labels = lvl.get("dimension_labels", {})
        descriptions = lvl.get("dimension_descriptions", {})
        dim_lines = "\n".join(
            f"- {c}: {labels.get(c, c)}" + (f" ({descriptions[c]})" if descriptions.get(c) else "")
            for c in codes
        )
        task = _LEVEL_TASK_TEMPLATE.format(
            level_id=lvl["id"],
            level_name=lvl.get("name", lvl["id"]),
            level_description=lvl.get("description", ""),
            dimension_list=dim_lines,
        )
        full_pair = ", ".join(f'"{c}": <1-9 int>' for c in codes)
        instruction = _PANEL_LEVEL_INSTRUCTION_TEMPLATE.format(level_id=lvl["id"], full_pair=full_pair)

        user_parts = [task, instruction]
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
            # _validate_level_fields() accumulates its own per-level error
            # list internally, gating its self-rating checks on "no problems
            # in THIS level" rather than on the shared `errors` list below —
            # gating on `errors` directly used to mean that once level 1
            # produced any error, every later level's self-rating check
            # (`best_to_others[best] must be 1`) was silently skipped for
            # the rest of this parse call, surfacing at most one such error
            # per response no matter how many levels actually had it.
            # Against a model with one systematic misconvention repeated
            # identically across every level (rating self-comparisons as 9
            # instead of 1), that meant the reject-and-repair loop could
            # only ever whack one mole per retry and never converged within
            # its retry budget, so the whole agent, and often the whole
            # panel, ended up `accepted_count: 0` in production even though
            # every rejected sample was one small, repair-loop-fixable
            # convention mistake.
            if lid not in level_answers:
                errors.append(f"Missing level '{lid}'")
                continue
            answer = level_answers[lid]
            if not isinstance(answer, dict):
                errors.append(f"Level '{lid}' answer must be an object")
                continue
            errors.extend(self._validate_level_fields(lid, codes, answer))

        if "sources_used" in data and not isinstance(data["sources_used"], list):
            errors.append(f"sources_used must be a list, got {type(data['sources_used']).__name__}")

        return InstrumentResult(valid=not errors, payload=data, errors=errors)

    @staticmethod
    def _validate_level_fields(lid: str, codes: set, answer: Dict[str, Any]) -> List[str]:
        """Per-level field/value validation, shared by parse() (validating
        every level in one whole-response blob) and validate_level() (Phase
        3's per-level "survey_panel" flow, validating one level's submitted
        answer in isolation). One shared function is what keeps the two
        callers' error messages identical; it is not a coincidental
        duplication that happened to be extractable."""
        level_errors: List[str] = []
        for key in ("best", "worst", "best_to_others", "others_to_worst"):
            if key not in answer:
                level_errors.append(f"Level '{lid}' missing key '{key}'")
        if level_errors:
            return level_errors

        if answer["best"] not in codes:
            level_errors.append(f"Level '{lid}': best='{answer['best']}' is not a known code {sorted(codes)}")
        if answer["worst"] not in codes:
            level_errors.append(f"Level '{lid}': worst='{answer['worst']}' is not a known code {sorted(codes)}")
        if answer.get("best") == answer.get("worst"):
            level_errors.append(f"Level '{lid}': best and worst must differ")

        for field_name in ("best_to_others", "others_to_worst"):
            vec = answer.get(field_name, {})
            if not isinstance(vec, dict):
                level_errors.append(f"Level '{lid}': {field_name} must be an object")
                continue
            missing = codes - set(vec)
            if missing:
                level_errors.append(f"Level '{lid}': {field_name} missing ratings for {sorted(missing)}")
            for code, value in vec.items():
                if not isinstance(value, int) or isinstance(value, bool) or not (1 <= value <= 9):
                    level_errors.append(f"Level '{lid}': {field_name}[{code}]={value!r} is not an integer in 1-9")

        if not level_errors and answer.get("best") in codes:
            bto = answer["best_to_others"].get(answer["best"])
            if bto != 1:
                level_errors.append(f"Level '{lid}': best_to_others[best] must be 1, got {bto}")
        if not level_errors and answer.get("worst") in codes:
            otw = answer["others_to_worst"].get(answer["worst"])
            if otw != 1:
                level_errors.append(f"Level '{lid}': others_to_worst[worst] must be 1, got {otw}")

        return level_errors

    def validate_level(self, level_id: str, answer: Dict[str, Any], params: Dict[str, Any]) -> InstrumentResult:
        """Validate ONE level's answer in isolation, independent of every
        other level's state — the core primitive Phase 3's InstrumentSubmit
        tool (tools/registry.py) calls from inside an OpenManus
        "survey_panel" flow run, so a convention mistake on one level can be
        caught and corrected in a couple of tool-call turns instead of
        costing a whole multi-level response's reject-and-repair retry (see
        parse()'s comment above on why whole-response retries converged
        poorly against a model with one systematic per-level mistake)."""
        levels_by_id = {lvl["id"]: lvl for lvl in self._levels(params)}
        if level_id not in levels_by_id:
            return InstrumentResult(valid=False, payload={level_id: answer}, errors=[f"Unknown level '{level_id}'"])
        codes = set(levels_by_id[level_id]["dimensions"])
        if not isinstance(answer, dict):
            return InstrumentResult(valid=False, payload={level_id: answer}, errors=[f"Level '{level_id}' answer must be an object"])
        errors = self._validate_level_fields(level_id, codes, answer)
        return InstrumentResult(valid=not errors, payload={level_id: answer}, errors=errors)
