"""Setup-review meta-instrument: a pipeline-stage agent's judgment-level
review of a survey's own configuration, layered on top of the deterministic
checks `survey_checks.py::fix_survey()` and `preflight.py` already do.

Those two modules are, and stay, the correct place for anything that has a
single objectively-correct answer (a missing field, a dangling path, an
unreachable provider): cheap, deterministic, no hallucination risk. This
instrument exists only for the judgment calls a schema check cannot make:
does the dimension set actually cover the construct being measured, does an
agent's role_description fit its assigned RAG corpus/rulefile, are two roles
redundant. `spawning/pipeline.py` always runs the deterministic checks first
and hands their output to this instrument as already-known information, so
the agent is told not to re-report them.

This is a review, not a repair tool: the schema below asks for findings and
proposed fixes as text, never for permission to edit files. See
`spawning/pipeline.py` for why: "AI has no authority to decide intent"
applies here as much as to anything else in this repo, and a survey's own
config is a human-authored artifact this app must not silently rewrite.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List

from .base import InstrumentResult

_VALID_SEVERITIES = {"info", "warning", "blocker"}

_TASK_TEMPLATE = """\
You are reviewing one research survey's own configuration for methodological \
and consistency problems that a schema/path checker cannot catch, before it \
is run against a real panel of agents. This is a judgment review, not a \
repair tool: propose fixes as text, you cannot and must not edit any file \
yourself.

Deterministic structural checks already ran and found these problems (do not \
repeat them, they are already known and already reported separately):
{deterministic_problems}

Survey manifest (survey.yaml):
```yaml
{survey_yaml_text}
```

Agent cards configured for this survey's panel:
{agent_cards_text}

Review for things a schema check cannot catch, for example: whether the \
configured dimensions actually cover the construct the survey title/description \
claims to measure; whether an agent's role_description is a good fit for its \
assigned RAG corpus, rulefile, or role_pack; whether two agents' roles are so \
similar they add no real diversity to the panel; whether the task_template (if \
any) or dimension_labels could plausibly confuse a model about the required \
output schema. Ground every finding in the actual content shown above; never \
invent a detail about the survey that was not actually shown to you.

If you find nothing beyond what the deterministic checks already caught, \
return an empty findings list; do not invent a problem just to have something \
to say.

Respond with ONLY a JSON object, no other text, in exactly this shape:
{{
  "findings": [
    {{
      "severity": "info" | "warning" | "blocker",
      "area": "<short area tag, e.g. 'dimensions', 'agent:reviewer-1', 'rulefile'>",
      "finding": "<the actual problem, specific and grounded in what was shown above>",
      "proposed_fix": "<a concrete suggested change; not a file edit, just what a human should change>"
    }}
  ],
  "summary": "<one or two sentences: does this survey look ready to run>"
}}
"""


def _format_agent_cards(agent_cards_text: List[str]) -> str:
    if not agent_cards_text:
        return "(no agent cards were provided)"
    parts = []
    for i, text in enumerate(agent_cards_text):
        parts.append(f"```json\n{text}\n```")
    return "\n\n".join(parts)


def _format_deterministic_problems(problems: List[str]) -> str:
    if not problems:
        return "(none found)"
    return "\n".join(f"- {p}" for p in problems)


class SetupReviewInstrument:
    name = "setup_review"

    def build_messages(
        self,
        agent_role_description: str,
        context_chunks: List[str],
        params: Dict[str, Any],
    ) -> List[Dict[str, str]]:
        task = _TASK_TEMPLATE.format(
            deterministic_problems=_format_deterministic_problems(params.get("deterministic_problems", [])),
            survey_yaml_text=params.get("survey_yaml_text", ""),
            agent_cards_text=_format_agent_cards(params.get("agent_cards_text", [])),
        )
        user_parts = [task]
        if context_chunks:
            joined = "\n\n---\n\n".join(context_chunks)
            user_parts.append(f"\nAdditional reference material:\n\n{joined}")
        return [
            {"role": "system", "content": agent_role_description},
            {"role": "user", "content": "\n".join(user_parts)},
        ]

    def parse(self, raw_text: str, params: Dict[str, Any]) -> InstrumentResult:
        errors: List[str] = []
        match = re.search(r"\{.*\}", raw_text, re.DOTALL)
        if not match:
            return InstrumentResult(valid=False, payload={}, errors=["No JSON object found in response"])
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            return InstrumentResult(valid=False, payload={}, errors=[f"JSON parse error: {exc}"])

        if "findings" not in data:
            errors.append("Missing key 'findings'")
        elif not isinstance(data["findings"], list):
            errors.append("'findings' must be a list")
        else:
            for i, finding in enumerate(data["findings"]):
                if not isinstance(finding, dict):
                    errors.append(f"findings[{i}] must be an object")
                    continue
                for key in ("severity", "area", "finding", "proposed_fix"):
                    if key not in finding:
                        errors.append(f"findings[{i}] missing key '{key}'")
                if finding.get("severity") not in _VALID_SEVERITIES:
                    errors.append(
                        f"findings[{i}].severity={finding.get('severity')!r} not in {sorted(_VALID_SEVERITIES)}"
                    )

        if "summary" not in data:
            errors.append("Missing key 'summary'")

        return InstrumentResult(valid=not errors, payload=data, errors=errors)
