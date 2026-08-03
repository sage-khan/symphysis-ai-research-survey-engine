"""Natural-language agent proposal: "describe what kind of panel you need,
in plain English, and get a reviewable list of agents back" -- either
reusing an existing Agent Library entry or proposing a brand new one.

Deliberately named differently from `agentic_survey.orchestrator` (which
drives an already-configured survey's actual run): this module never
drives a survey run and never creates anything by itself. It only proposes
a JSON structure for a human to review, edit, and explicitly approve
(`routers/proposer.py`'s two-endpoint flow) -- nothing here writes an Agent
Card to disk. If the model's response can't be parsed as valid proposals,
that is surfaced as an error, never silently replaced with a plausible-
looking fabrication.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List

_SYSTEM_PROMPT = """\
You are an orchestrator that assembles expert-review panels of AI agents \
for a structured survey / expert-elicitation task. Given the user's plain- \
language requirement, the survey this panel is for, and the list of \
already-available library agents, propose a panel: for each agent, decide \
whether an existing library agent is a good fit (reuse it) or a new one \
should be created.

Respond with ONLY a JSON array, no other text, in exactly this shape:
[
  {"source": "library", "agent_id": "<id of an existing library agent to reuse, must be one from the list below>"},
  {"source": "new", "agent_id": "<new, unique, kebab-case id>", "display_name": "<a human name or persona label>", "role": "<short role title>", "expertise": "<one-line profession/expertise summary>", "role_description": "<1-3 sentence professional persona>", "model": {"provider": "ollama", "name": "<a real model name>"}}
]

Rules:
- Every "new" entry's model.provider must be one of: ollama, anthropic, openai, openrouter, groq, gemini, xai. Prefer "ollama" with a locally-available model unless the requirement clearly calls for a specific hosted model.
- Every "library" entry's agent_id MUST be one of the ids listed below -- never invent one.
- Propose between 1 and 8 agents, covering distinct, non-redundant professional perspectives relevant to the requirement and the survey's criteria.
- Do not propose two "new" agents with the same agent_id, and do not propose a "new" agent whose agent_id collides with an existing library agent_id.
"""


def _build_user_prompt(requirement: str, survey_context: Dict[str, Any], library_agents: List[Dict[str, Any]]) -> str:
    criteria = survey_context.get("dimensions") or []
    lib_lines = (
        "\n".join(f"- {a['agent_id']}: {a.get('role', '')} ({a.get('provider', '')}/{a.get('model', '')})" for a in library_agents)
        or "(none yet -- every proposal should be \"new\")"
    )
    return (
        f"Survey: {survey_context.get('title', '(untitled)')}\n"
        f"Survey description: {survey_context.get('description') or '(none given)'}\n"
        f"Criteria being weighed: {', '.join(criteria) if criteria else '(none given)'}\n\n"
        f"Available library agents:\n{lib_lines}\n\n"
        f"User's requirement:\n{requirement}\n"
    )


def _ollama_models_available() -> List[str]:
    import os

    import requests

    base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    try:
        resp = requests.get(f"{base_url}/api/tags", timeout=5)
        resp.raise_for_status()
        return [m["name"] for m in resp.json().get("models", [])]
    except requests.RequestException:
        return []


class ProposalError(Exception):
    """Raised when the model's response can't be parsed into valid
    proposals. Carries the raw text so the caller can show the user
    exactly what came back, rather than a generic failure message."""

    def __init__(self, message: str, raw_text: str = "") -> None:
        super().__init__(message)
        self.raw_text = raw_text


def parse_proposals(raw_text: str, known_library_ids: List[str]) -> List[Dict[str, Any]]:
    match = re.search(r"\[.*\]", raw_text, re.DOTALL)
    if not match:
        raise ProposalError("No JSON array found in the orchestrator's response.", raw_text)
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        raise ProposalError(f"Could not parse the orchestrator's response as JSON: {exc}", raw_text) from exc
    if not isinstance(data, list) or not data:
        raise ProposalError("The orchestrator's response was not a non-empty JSON array.", raw_text)

    seen_new_ids = set()
    for i, entry in enumerate(data):
        if not isinstance(entry, dict) or "source" not in entry or "agent_id" not in entry:
            raise ProposalError(f"Entry {i} is missing 'source' or 'agent_id'.", raw_text)
        if entry["source"] == "library":
            if entry["agent_id"] not in known_library_ids:
                raise ProposalError(
                    f"Entry {i} proposes reusing library agent '{entry['agent_id']}', which doesn't exist.", raw_text
                )
        elif entry["source"] == "new":
            for required in ("role", "role_description", "model"):
                if required not in entry:
                    raise ProposalError(f"Entry {i} (new agent '{entry.get('agent_id')}') is missing '{required}'.", raw_text)
            if not isinstance(entry["model"], dict) or "provider" not in entry["model"] or "name" not in entry["model"]:
                raise ProposalError(f"Entry {i}'s model must have 'provider' and 'name'.", raw_text)
            if entry["agent_id"] in seen_new_ids or entry["agent_id"] in known_library_ids:
                raise ProposalError(f"Entry {i} reuses agent_id '{entry['agent_id']}', which must be unique.", raw_text)
            seen_new_ids.add(entry["agent_id"])
        else:
            raise ProposalError(f"Entry {i} has source={entry['source']!r}, must be 'library' or 'new'.", raw_text)
    return data


def propose_agents(
    requirement: str,
    survey_context: Dict[str, Any],
    library_agents: List[Dict[str, Any]],
    provider: str,
    model: str,
) -> List[Dict[str, Any]]:
    from agentic_survey.providers import get_provider

    llm = get_provider(provider)
    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": _build_user_prompt(requirement, survey_context, library_agents)},
    ]
    response = llm.complete(messages, model=model, temperature=0.4, max_tokens=2048, top_p=1.0, seed=None)
    known_ids = [a["agent_id"] for a in library_agents]
    proposals = parse_proposals(response.text, known_ids)
    _annotate_model_availability(proposals)
    return proposals


def _annotate_model_availability(proposals: List[Dict[str, Any]]) -> None:
    """The orchestrator LLM can (and does, observed live) hallucinate a
    plausible-sounding but non-existent Ollama model name (e.g. proposing
    "code-davinci" as an "ollama" model). That's not caught by
    parse_proposals's schema validation -- it's a real model name, just not
    one actually pulled on this Ollama host. Rather than silently letting
    that through (where it would only fail once the survey is actually run,
    long after approval) or silently rejecting the whole proposal (the
    model list is a live, mutable fact the human reviewing it can just as
    easily fix), annotate each "new" ollama entry with whether its model is
    currently available, so the review UI can flag it and a human decides
    what to do -- pick a real model, or leave it and pull that model first."""
    new_ollama_entries = [p for p in proposals if p.get("source") == "new" and p.get("model", {}).get("provider") == "ollama"]
    if not new_ollama_entries:
        return
    available = set(_ollama_models_available())
    for entry in new_ollama_entries:
        entry["model_available"] = (not available) or (entry["model"]["name"] in available)
