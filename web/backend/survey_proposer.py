"""Natural-language survey proposal: "describe the study you want to run,
in plain English, and get a reviewable draft back" (title, description,
instrument choice with justification, and a criteria list), the same
propose-then-approve shape agent_proposer.py already uses for agents.

Nothing here creates a survey. It only proposes a JSON structure for a
human to review, edit, and explicitly submit through the existing
POST /api/surveys endpoint. If the model's response can't be parsed, that
is surfaced as an error, never silently replaced with a fabrication.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict

_KNOWN_INSTRUMENTS = {"bwm", "ahp"}

_SYSTEM_PROMPT = """\
You are a research methodology assistant helping a researcher turn a plain-language \
description of a study into a structured expert-elicitation survey configuration.

Two instruments are available:
- "bwm" (Best-Worst Method): each expert names the single most and least important \
criterion, then rates every criterion's importance relative to those two. Efficient \
for a moderate number of criteria (roughly 3-10), gives one linear program per expert.
- "ahp" (Analytic Hierarchy Process): each expert rates every PAIR of criteria against \
each other on a 1-9 scale. More thorough and better at catching an expert's own \
inconsistency (via a formal consistency ratio), but the number of pairs grows \
quadratically, so it becomes burdensome above roughly 6-7 criteria.

Given the researcher's plain-language description of their study, propose: a concise \
title, a one-sentence description, which instrument fits better and why, and a list of \
the criteria (dimensions) the study should weigh, each with a short unique code (2-4 \
uppercase letters) and a clear label.

Respond with ONLY a JSON object, no other text, in exactly this shape:
{
  "title": "<concise study title>",
  "description": "<one sentence, what this survey is weighing and why>",
  "instrument": "bwm" or "ahp",
  "instrument_justification": "<1-2 sentences explaining why this instrument fits, referencing the number of criteria and the study's actual goal>",
  "criteria": [{"code": "<CODE>", "label": "<human-readable label>"}, ...]
}

Propose between 3 and 8 criteria. Every code must be unique. Do not invent domain facts \
about the researcher's field beyond what a reasonable methodologist would know; if the \
description is vague, propose a reasonable, generic set of criteria for that kind of \
study and say so plainly in the description rather than inventing specifics you were \
not given.
"""


class SurveyProposalError(Exception):
    """Raised when the model's response can't be parsed into a valid
    survey draft. Carries the raw text so the caller can show the user
    exactly what came back, rather than a generic failure message."""

    def __init__(self, message: str, raw_text: str = "") -> None:
        super().__init__(message)
        self.raw_text = raw_text


def parse_survey_proposal(raw_text: str) -> Dict[str, Any]:
    match = re.search(r"\{.*\}", raw_text, re.DOTALL)
    if not match:
        raise SurveyProposalError("No JSON object found in the proposer's response.", raw_text)
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        raise SurveyProposalError(f"Could not parse the proposer's response as JSON: {exc}", raw_text) from exc

    for required in ("title", "description", "instrument", "instrument_justification", "criteria"):
        if required not in data:
            raise SurveyProposalError(f"Response is missing '{required}'.", raw_text)

    if data["instrument"] not in _KNOWN_INSTRUMENTS:
        raise SurveyProposalError(
            f"Response proposes instrument={data['instrument']!r}, must be one of {sorted(_KNOWN_INSTRUMENTS)}.", raw_text
        )

    criteria = data["criteria"]
    if not isinstance(criteria, list) or not criteria:
        raise SurveyProposalError("'criteria' must be a non-empty list.", raw_text)

    seen_codes = set()
    for i, c in enumerate(criteria):
        if not isinstance(c, dict) or "code" not in c or "label" not in c:
            raise SurveyProposalError(f"criteria[{i}] is missing 'code' or 'label'.", raw_text)
        if c["code"] in seen_codes:
            raise SurveyProposalError(f"criteria[{i}] reuses code '{c['code']}', codes must be unique.", raw_text)
        seen_codes.add(c["code"])

    return data


def propose_survey_concept(concept: str, provider: str, model: str) -> Dict[str, Any]:
    from symphysis.providers import get_provider

    llm = get_provider(provider)
    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": f"Study description:\n{concept}\n"},
    ]
    response = llm.complete(messages, model=model, temperature=0.4, max_tokens=1536, top_p=1.0, seed=None)
    return parse_survey_proposal(response.text)
