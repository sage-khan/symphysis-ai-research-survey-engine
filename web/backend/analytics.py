"""Weight-elicitation analytics: who said what, and who didn't.

Pure filesystem-derived aggregation, no FastAPI dependency, so it's directly
unit-testable and so the router stays thin (HTTP in, JSON out).

A survey's `agents/<id>.json` lists every *configured* agent; not every one
necessarily produced data. This module classifies each configured agent into
exactly one status, purely from what's actually on disk. It never assumes
"configured" means "ran", and never fabricates a result for an agent that
didn't produce one:

- ``contributed``: `agents/<id>/result.json` exists with accepted_count > 0.
- ``zero_accepted``: `result.json` exists but accepted_count == 0 and
  rejected_count > 0: the agent ran to completion but every sample was
  rejected by guardrails (e.g. malformed JSON, a "thinking" model spending
  its whole token budget before an answer, missing a required rating).
- ``pending_manual``: `result.json` exists with accepted_count == 0 and
  rejected_count == 0, and a `manual_input/prompt_*.md` file is waiting to
  be answered: a manual-provider agent that hasn't been given its pasted
  response(s) yet.
- ``skipped``: no `result.json` at all, even though the agent's runtime
  folder exists: the orchestrator caught a ProviderError/PermissionError_/
  AgentCardError before any sample could be attempted (most commonly: no
  API key configured for that provider) and moved on to the next agent.
- ``not_run``: the agent is configured but the survey has never been run
  (no runtime folder at all).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def compute_analytics(survey_dir: Path) -> Dict[str, Any]:
    agents_dir = survey_dir / "agents"
    per_agent: List[Dict[str, Any]] = []
    best_count: Dict[str, int] = {}
    worst_count: Dict[str, int] = {}
    counts = {"contributed": 0, "zero_accepted": 0, "pending_manual": 0, "skipped": 0, "not_run": 0}

    for card_path in sorted(agents_dir.glob("*.json")):
        card = _read_json(card_path)
        agent_id = card["agent_id"]
        runtime_dir = agents_dir / agent_id
        entry: Dict[str, Any] = {
            "agent_id": agent_id,
            "display_name": card.get("display_name"),
            "role": card.get("role"),
            "provider": card.get("model", {}).get("provider"),
            "model": card.get("model", {}).get("name"),
            "rag_enabled": card.get("rag", {}).get("enabled", False),
            "did": card.get("did", {}).get("id"),
            "samples": [],
        }

        if not runtime_dir.is_dir():
            entry["status"] = "not_run"
            entry["detail"] = "Survey has not been run since this agent was added."
            counts["not_run"] += 1
            per_agent.append(entry)
            continue

        result_path = runtime_dir / "result.json"
        if not result_path.exists():
            entry["status"] = "skipped"
            entry["detail"] = (
                "No result.json was ever written for this agent: the orchestrator caught a "
                "provider, permission, or agent-card error before any sample could be attempted "
                "(most commonly a missing API key for this provider) and moved on."
            )
            counts["skipped"] += 1
            per_agent.append(entry)
            continue

        result = _read_json(result_path)
        accepted = result.get("accepted_payloads", [])
        rejected_count = result.get("rejected_count", 0)
        manual_pending = sorted((runtime_dir / "manual_input").glob("prompt_*.md")) if (runtime_dir / "manual_input").exists() else []

        if accepted:
            entry["status"] = "contributed"
            counts["contributed"] += 1
            for i, payload in enumerate(accepted):
                entry["samples"].append(
                    {
                        "index": i,
                        "best": payload.get("best"),
                        "worst": payload.get("worst"),
                        "best_to_others": payload.get("best_to_others"),
                        "others_to_worst": payload.get("others_to_worst"),
                        "reasoning": payload.get("reasoning"),
                    }
                )
                if payload.get("best"):
                    best_count[payload["best"]] = best_count.get(payload["best"], 0) + 1
                if payload.get("worst"):
                    worst_count[payload["worst"]] = worst_count.get(payload["worst"], 0) + 1
        elif manual_pending and rejected_count == 0:
            entry["status"] = "pending_manual"
            entry["detail"] = f"{len(manual_pending)} prompt(s) waiting for a pasted-back response."
            counts["pending_manual"] += 1
        else:
            entry["status"] = "zero_accepted"
            entry["detail"] = (
                f"Ran to completion but every one of {rejected_count} attempt(s) was rejected by "
                "guardrails (schema validation, denylist, or repeated-sampling checks); see this "
                "agent's Trace / Conversation log for the exact rejection reasons."
            )
            counts["zero_accepted"] += 1

        per_agent.append(entry)

    criteria = sorted(set(best_count) | set(worst_count))
    frequency = [
        {"criterion": c, "best_count": best_count.get(c, 0), "worst_count": worst_count.get(c, 0)} for c in criteria
    ]

    return {
        "summary": counts,
        "best_worst_frequency": frequency,
        "per_agent": per_agent,
    }
