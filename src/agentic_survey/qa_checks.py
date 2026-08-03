"""Genuineness checks: verifying an agent's stated identity and cited
sources against ground truth, instead of trusting a model's self-report.

Two checks live here:

1. The QA precheck (see Agent.run_qa_precheck in agent.py): before an agent
   attempts the actual survey, it is told its own real configuration and
   asked to restate it. This module compares that restatement against the
   ground truth field by field.
2. Sources-used verification (see BWMInstrument and Agent._context_chunks):
   an agent's answer states which reference-material tags it actually drew
   on. This module checks each claimed tag against the tags that were
   genuinely present in that agent's prompt, so a claimed source that was
   never actually provided is caught, not trusted.

Both checks are deterministic string and set comparisons, not further model
calls. Verifying a claim with another possibly-hallucinating model call
would not be a genuine check.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

_TAG_RE = re.compile(r"^\[([^\]]+)\]")

GENERAL_KNOWLEDGE_TAG = "general_knowledge"


def extract_source_tags(context_chunks: List[str]) -> List[str]:
    """The distinct bracket tags (for example "role knowledge: data_engineer"
    or "shared knowledge: kb_marker.md") actually present in this agent's
    reference material, in first-seen order, always ending with the
    always-available general_knowledge option."""
    tags: List[str] = []
    for chunk in context_chunks:
        m = _TAG_RE.match(chunk)
        if m and m.group(1) not in tags:
            tags.append(m.group(1))
    tags.append(GENERAL_KNOWLEDGE_TAG)
    return tags


def verify_sources_used(claimed: Any, available_tags: List[str]) -> Dict[str, Any]:
    """Check a response's self-reported sources_used list against what was
    genuinely available in that prompt. A claimed tag absent from
    available_tags is a fabricated citation: the agent said it used
    reference material it was never actually given."""
    if not isinstance(claimed, list):
        return {
            "claimed": claimed,
            "available_tags": available_tags,
            "fabricated": [],
            "reported": False,
            "genuine": None,
        }
    fabricated = [c for c in claimed if c not in available_tags]
    return {
        "claimed": claimed,
        "available_tags": available_tags,
        "fabricated": fabricated,
        "reported": True,
        "genuine": len(fabricated) == 0,
    }


def build_precheck_ground_truth(
    agent_id: str,
    role: str,
    provider: str,
    model_name: str,
    has_dedicated_rag: bool,
    has_shared_knowledge_repo: bool,
    role_pack: Optional[str],
    has_web_search: bool,
) -> Dict[str, Any]:
    """The real configuration this agent was actually given, computed from
    its AgentCard and the retrievers Agent.__init__ actually built. Never
    computed from what a model claims about itself."""
    return {
        "agent_id": agent_id,
        "role": role,
        "model": f"{provider}/{model_name}",
        "capabilities": {
            "dedicated_rag_corpus": has_dedicated_rag,
            "shared_knowledge_repo": has_shared_knowledge_repo,
            "role_pack": role_pack,
            "web_search": has_web_search,
        },
    }


def verify_precheck_response(claimed: Any, ground_truth: Dict[str, Any]) -> Dict[str, Any]:
    """Field-by-field comparison of what the agent restated against its real
    configuration. Every field is a strict comparison (case-insensitive,
    whitespace-trimmed for free-text fields) since the agent was just told
    the exact ground truth values moments before answering. Any mismatch is
    either a hallucinated capability or a comprehension failure, both worth
    surfacing to a reviewer, not silently accepted."""
    if not isinstance(claimed, dict):
        checks = {
            "agent_id": False,
            "role": False,
            "model": False,
            "dedicated_rag_corpus": False,
            "shared_knowledge_repo": False,
            "role_pack": False,
            "web_search": False,
        }
        return {"ground_truth": ground_truth, "claimed": claimed, "field_matches": checks, "all_match": False}

    claimed_caps = claimed.get("capabilities", {})
    if not isinstance(claimed_caps, dict):
        claimed_caps = {}
    truth_caps = ground_truth["capabilities"]

    def _norm(value: Any) -> Any:
        return value.strip().casefold() if isinstance(value, str) else value

    checks = {
        "agent_id": _norm(claimed.get("agent_id")) == _norm(ground_truth["agent_id"]),
        "role": _norm(claimed.get("role")) == _norm(ground_truth["role"]),
        "model": _norm(claimed.get("model")) == _norm(ground_truth["model"]),
        "dedicated_rag_corpus": claimed_caps.get("dedicated_rag_corpus") == truth_caps["dedicated_rag_corpus"],
        "shared_knowledge_repo": claimed_caps.get("shared_knowledge_repo") == truth_caps["shared_knowledge_repo"],
        "role_pack": _norm(claimed_caps.get("role_pack")) == _norm(truth_caps["role_pack"]),
        "web_search": claimed_caps.get("web_search") == truth_caps["web_search"],
    }
    return {
        "ground_truth": ground_truth,
        "claimed": claimed,
        "field_matches": checks,
        "all_match": all(checks.values()),
    }
