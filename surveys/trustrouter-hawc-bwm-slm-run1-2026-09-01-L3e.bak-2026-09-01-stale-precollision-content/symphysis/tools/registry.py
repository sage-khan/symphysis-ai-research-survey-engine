"""Per-agent tool registry: the set of real, callable tools an agent's
granted capabilities entitle it to use, decoupled from which runtime
backend actually invokes them — `agent.py`'s own one-shot context assembly
today (`_rag_chunks`/`_web_search_chunks`/`_knowledge_repo_chunks`), or an
OpenManus `SurveyElicitationAgent`'s multi-turn tool loop reached through
`tools/proxy.py` (plan doc Phase 2 task 15).

Building this registry never constructs a new retriever: each `ToolSpec`
wraps the SAME retriever instance `Agent.__init__` already built
(`agent._retriever` / `agent._knowledge_repo_retriever`), so a RAG corpus is
embedded/indexed exactly once per agent run regardless of which backend
ends up calling it. Reaching into those attributes directly (rather than
turning them into public API) is a deliberate, minimal-diff choice: this
module lives in the same package as `agent.py` and exists specifically to
expose what `Agent` already built, not to duplicate or re-derive it.

Every `execute` function here logs via `storage.write_tool_call` with the
exact same `tool=`/`detail=` shape `agent.py`'s own `_rag_chunks` etc.
already use, so an OpenManus-driven run's trail entries render identically
in `TraceViewer.jsx` to a direct-completion run's — a reviewer should not
be able to tell which backend produced a given `tool_call` entry just by
looking at its shape.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional

from .. import qa_checks
from ..agent import KNOWLEDGE_REPO_DIRNAME
from ..policy.capability import KNOWLEDGE_REPO, RAG_RETRIEVAL, WEB_SEARCH
from .web_search import WebSearchError, search_as_dicts

if TYPE_CHECKING:
    from ..agent import Agent

_QUERY_TOP_K_PARAMETERS = {
    "type": "object",
    "properties": {
        "query": {"type": "string", "description": "The search query."},
        "top_k": {"type": "integer", "description": "How many results to retrieve."},
    },
    "required": ["query"],
}

_CITATION_VERIFY_PARAMETERS = {
    "type": "object",
    "properties": {
        "claimed": {
            "type": "array",
            "items": {"type": "string"},
            "description": "The source tags you are claiming to have used.",
        },
        "available_tags": {
            "type": "array",
            "items": {"type": "string"},
            "description": "The source tags that were genuinely available in this prompt.",
        },
    },
    "required": ["claimed", "available_tags"],
}

_INSTRUMENT_SUBMIT_PARAMETERS = {
    "type": "object",
    "properties": {
        "level_id": {"type": "string", "description": "Which level this submission answers, e.g. \"L1\"."},
        "best": {"type": "string", "description": "The code of the single best (most important) criterion in this level."},
        "worst": {"type": "string", "description": "The code of the single worst (least important) criterion in this level."},
        "best_to_others": {"type": "object", "description": "Ratio (1-9 int) of best vs. every criterion in this level, keyed by code."},
        "others_to_worst": {"type": "object", "description": "Ratio (1-9 int) of every criterion vs. worst in this level, keyed by code."},
        "reasoning": {"type": "string", "description": "Your reasoning for this level's ratings."},
    },
    "required": ["level_id", "best", "worst", "best_to_others", "others_to_worst"],
}


@dataclass
class ToolSpec:
    name: str
    capability: Optional[str]  # None = no capability gate (e.g. citation_verify)
    execute: Callable[..., Dict[str, Any]]  # kwargs from the caller -> JSON-serializable result
    description: str = ""
    # JSON-schema `parameters` object, in OpenAI function-calling shape.
    # Populated for every tool below so tools/proxy.py's caller
    # (runtime/openmanus.py::OpenManusProvider) can hand OpenManus's
    # ProxyTool the same schema this registry itself considers correct,
    # rather than a second, hand-maintained copy living in runtime/.
    parameters: Dict[str, Any] = None


def build_registry(
    agent: "Agent",
    *,
    instrument: Optional[Any] = None,
    instrument_params: Optional[Dict[str, Any]] = None,
) -> Dict[str, ToolSpec]:
    """One registry per agent run. Only includes a tool the agent's card
    actually supports (a RAG tool is present only if `agent._retriever` was
    built, i.e. `card.rag.enabled`); `tools/authorization.py`'s capability
    check is the actual gate on whether a call is *permitted*, this is
    just which tools *exist* for this agent to be gated on at all.

    `instrument`/`instrument_params` are optional and only used to register
    `instrument_submit` (Phase 3's per-level "survey_panel" flow, see
    docs/architecture/governance-layer-and-runtime-backends-plan.md):
    duck-typed on `hasattr(instrument, "validate_level")` rather than an
    isinstance check against `HierarchicalBWMInstrument` specifically, so
    any future instrument that implements the same per-level validation
    contract gets this tool for free without this module needing to know
    about it by name."""
    registry: Dict[str, ToolSpec] = {}

    if agent._retriever is not None:

        def _rag_retrieval(query: str, top_k: Optional[int] = None, _agent=agent) -> Dict[str, Any]:
            k = top_k or _agent.card.rag.top_k
            chunks = _agent._retriever.top_k(query, k)
            _agent.storage.write_tool_call(
                _agent.card.agent_id,
                tool="rag_retrieval",
                detail={
                    "corpus_path": _agent.card.rag.corpus_path,
                    "query": query,
                    "top_k": k,
                    "retrieved_sources": [c.source for c in chunks],
                },
            )
            return {"chunks": [{"source": c.source, "text": c.text} for c in chunks]}

        registry["rag_retrieval"] = ToolSpec(
            name="rag_retrieval",
            capability=RAG_RETRIEVAL,
            execute=_rag_retrieval,
            description="Retrieve the top-k most relevant passages from this agent's own dedicated RAG corpus for a query.",
            parameters=_QUERY_TOP_K_PARAMETERS,
        )

    if agent._knowledge_repo_retriever is not None:

        def _knowledge_repo(query: str, top_k: int = 5, _agent=agent) -> Dict[str, Any]:
            chunks = _agent._knowledge_repo_retriever.top_k(query, top_k)
            _agent.storage.write_tool_call(
                _agent.card.agent_id,
                tool="knowledge_repo_retrieval",
                detail={
                    "corpus_path": f"{KNOWLEDGE_REPO_DIRNAME}/ (shared, survey-level)",
                    "query": query,
                    "top_k": top_k,
                    "retrieved_sources": [c.source for c in chunks],
                },
            )
            return {"chunks": [{"source": c.source, "text": c.text} for c in chunks]}

        registry["knowledge_repo"] = ToolSpec(
            name="knowledge_repo",
            capability=KNOWLEDGE_REPO,
            execute=_knowledge_repo,
            description="Retrieve the top-k most relevant passages from this survey's shared knowledge repository for a query.",
            parameters=_QUERY_TOP_K_PARAMETERS,
        )

    if "web_search" in agent.card.tools:

        def _web_search(query: str, top_k: int = 5, _agent=agent) -> Dict[str, Any]:
            try:
                results = search_as_dicts(query, top_k=top_k)
            except WebSearchError as exc:
                # Matches agent.py's _web_search_chunks: an optional
                # grounding tool being unavailable is logged, not raised,
                # so the agent can proceed with whatever else it has.
                _agent.storage.write_tool_call(
                    _agent.card.agent_id, tool="web_search", detail={"query": query, "error": str(exc)}
                )
                return {"results": [], "error": str(exc)}
            _agent.storage.write_tool_call(
                _agent.card.agent_id, tool="web_search", detail={"query": query, "results": results}
            )
            return {"results": results}

        registry["web_search"] = ToolSpec(
            name="web_search",
            capability=WEB_SEARCH,
            execute=_web_search,
            description=(
                "Search the web for a query and return real results (title/url/content). "
                "Degrades gracefully (empty results plus an error field) if the search "
                "service is unavailable; never fabricate a result yourself if this returns nothing."
            ),
            parameters=_QUERY_TOP_K_PARAMETERS,
        )

    def _citation_verify(claimed, available_tags, _agent=agent) -> Dict[str, Any]:
        # Ungated (capability=None): checking a self-reported list against
        # what was genuinely available is not itself access to a protected
        # resource, exactly like agent.py's existing qa_checks calls are
        # never capability-gated either.
        result = qa_checks.verify_sources_used(claimed, available_tags)
        _agent.storage.write_tool_call(
            _agent.card.agent_id, tool="citation_verify", detail=result
        )
        return result

    registry["citation_verify"] = ToolSpec(
        name="citation_verify",
        capability=None,
        execute=_citation_verify,
        description=(
            "Check a self-reported list of claimed source tags against what was genuinely "
            "available, to catch a fabricated citation before finalizing an answer."
        ),
        parameters=_CITATION_VERIFY_PARAMETERS,
    )

    if instrument is not None and instrument_params is not None and hasattr(instrument, "validate_level"):

        def _instrument_submit(
            level_id: str,
            best: str,
            worst: str,
            best_to_others: Dict[str, Any],
            others_to_worst: Dict[str, Any],
            reasoning: str = "",
            _agent=agent,
            _instrument=instrument,
            _params=instrument_params,
        ) -> Dict[str, Any]:
            answer = {
                "best": best,
                "worst": worst,
                "best_to_others": best_to_others,
                "others_to_worst": others_to_worst,
                "reasoning": reasoning,
            }
            result = _instrument.validate_level(level_id, answer, _params)
            _agent.storage.write_tool_call(
                _agent.card.agent_id,
                tool="instrument_submit",
                detail={"level_id": level_id, "valid": result.valid, "errors": result.errors},
            )
            return {"valid": result.valid, "errors": result.errors}

        registry["instrument_submit"] = ToolSpec(
            name="instrument_submit",
            capability=None,  # a validation check against the agent's own answer, not a protected resource
            execute=_instrument_submit,
            description=(
                "Submit your completed answer for one instrument level for validation. Returns "
                "valid=true/false and, if false, the exact problems to fix before resubmitting."
            ),
            parameters=_INSTRUMENT_SUBMIT_PARAMETERS,
        )

    return registry
