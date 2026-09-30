"""Response-review meta-instrument: a pipeline-stage agent's second-pass
critique of the panel's own already-accepted responses, after a live run.

Distinct from the deterministic checks `guardrails.py` already enforces
(schema validity, denylist patterns, repeated-sampling agreement) and from
`qa_checks.py::verify_sources_used` (a mechanical claimed-vs-available check):
this instrument asks a model to read each accepted answer's reasoning against
its own numeric answer and flag anything that looks internally inconsistent,
under-justified, or suspicious in a way none of those mechanical checks can
catch. It never touches the accepted samples themselves; it only produces
findings for a human reviewer, appended to the survey's report.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List

from .base import InstrumentResult

_VALID_SEVERITIES = {"info", "warning", "blocker"}

_TASK_TEMPLATE = """\
You are the second-pass reviewer for one research survey's already-completed \
agent panel. Every response below already passed schema validation and \
repeated-sampling agreement checks; you are not re-checking that. Your job is \
to read each agent's own reasoning against its own numeric answer and flag \
anything a mechanical schema check cannot catch: reasoning that does not \
actually support the stated best/worst choice or ratings, reasoning that is a \
generic restatement of the task rather than real justification, or a claimed \
source that seems implausible given the reasoning shown.

Survey: {survey_title}
Instrument: {instrument}
Dimensions: {dimensions}

Accepted agent responses:
{agent_responses_text}

Ground every finding in the actual text shown above; never invent a detail \
about an agent's reasoning that was not actually shown to you. If a response \
looks genuinely sound, do not invent a problem just to have something to say \
about it.

Respond with ONLY a JSON object, no other text, in exactly this shape:
{{
  "findings": [
    {{
      "agent_id": "<the exact agent_id from the responses above>",
      "severity": "info" | "warning" | "blocker",
      "finding": "<the actual problem, specific and grounded in that agent's own reasoning/answer above>"
    }}
  ],
  "summary": "<one or two sentences: overall response quality across the panel>"
}}
"""


def _format_agent_responses(agent_responses: List[Dict[str, Any]]) -> str:
    if not agent_responses:
        return "(no accepted responses were provided)"
    parts = []
    for r in agent_responses:
        parts.append(
            f"### {r.get('agent_id')} (role: {r.get('role')})\n"
            f"Answer: {json.dumps(r.get('answer'))}\n"
            f"Reasoning: {r.get('reasoning')}"
        )
    return "\n\n".join(parts)


class ResponseReviewInstrument:
    name = "response_review"

    def build_messages(
        self,
        agent_role_description: str,
        context_chunks: List[str],
        params: Dict[str, Any],
    ) -> List[Dict[str, str]]:
        task = _TASK_TEMPLATE.format(
            survey_title=params.get("survey_title", ""),
            instrument=params.get("instrument", ""),
            dimensions=params.get("dimensions", []),
            agent_responses_text=_format_agent_responses(params.get("agent_responses", [])),
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
        known_agent_ids = {r.get("agent_id") for r in params.get("agent_responses", [])}
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
                for key in ("agent_id", "severity", "finding"):
                    if key not in finding:
                        errors.append(f"findings[{i}] missing key '{key}'")
                if finding.get("severity") not in _VALID_SEVERITIES:
                    errors.append(
                        f"findings[{i}].severity={finding.get('severity')!r} not in {sorted(_VALID_SEVERITIES)}"
                    )
                if finding.get("agent_id") is not None and finding.get("agent_id") not in known_agent_ids:
                    errors.append(
                        f"findings[{i}].agent_id={finding.get('agent_id')!r} is not one of the reviewed "
                        f"responses' agent_ids {sorted(a for a in known_agent_ids if a)}"
                    )

        if "summary" not in data:
            errors.append("Missing key 'summary'")

        return InstrumentResult(valid=not errors, payload=data, errors=errors)
