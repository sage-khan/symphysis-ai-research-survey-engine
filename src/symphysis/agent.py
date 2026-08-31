"""A single agent instance: identity (DID, from its Agent Card) + one
elicitation run, with permissions enforced from the same card."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import app_config, qa_checks, role_packs
from .agent_card import AgentCard
from .guardrails import GuardedRun, run_with_guardrails
from .instruments.base import Instrument
from .policy.authorization import check_data_scope, check_provider_allowed
from .providers import get_provider
from .rag.retriever import build_retriever
from .audit.logger import SurveyStorage
from .tools.web_search import WebSearchError, search_as_dicts

KNOWLEDGE_REPO_DIRNAME = "knowledge_repo"


def _has_retrievable_content(path: Path) -> bool:
    return path.is_dir() and (any(path.rglob("*.txt")) or any(path.rglob("*.md")))


def _extract_json_object(raw_text: str) -> Optional[Any]:
    """Best-effort JSON extraction from a raw completion, tolerant of a
    model wrapping its answer in prose. Returns None (never raises, never
    invents a value) if no JSON object is found or it doesn't parse, so a
    caller can log that failure as its own genuineness signal rather than
    crashing on a malformed QA precheck response."""
    match = re.search(r"\{.*\}", raw_text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


class Agent:
    def __init__(self, card: AgentCard, card_source: Path, storage: SurveyStorage) -> None:
        self.card = card
        self.storage = storage
        check_provider_allowed(card.model.provider, card.permissions)
        storage.init_agent(card, card_source)

        self._retriever = None
        if card.rag.enabled:
            check_data_scope(card.rag.corpus_path, card.permissions)
            self._retriever = build_retriever(
                card.rag.corpus_path, card.rag.chunk_size, card.rag.chunk_overlap, card.rag.embedding_model
            )

        # The survey's shared knowledge repository (uploaded once per
        # survey, distinct from any one agent's own dedicated RAG corpus)
        # is available to every agent in that survey automatically. No
        # per-agent flag is required, matching how a project's shared
        # reference material works for a human panel. Its absence (most
        # surveys won't have one) is the normal case, not an error, unlike
        # a misconfigured *dedicated* corpus_path.
        self._knowledge_repo_retriever = None
        knowledge_repo_path = self.storage.root / KNOWLEDGE_REPO_DIRNAME
        if _has_retrievable_content(knowledge_repo_path):
            rag_defaults = app_config.rag_defaults()
            self._knowledge_repo_retriever = build_retriever(
                str(knowledge_repo_path),
                rag_defaults.get("chunk_size", 800),
                rag_defaults.get("chunk_overlap", 100),
                rag_defaults.get("embedding_model"),
            )

    def _role_description(self) -> str:
        if self.card.system_prompt_override:
            # Literal, user-edited text (e.g. from the web UI's Agent panel):
            # not run through .format(), since free-typed text may contain
            # stray "{"/"}" that would raise on a template substitution never
            # intended to apply to it.
            base = self.card.system_prompt_override
        else:
            template_path = Path(self.card.system_prompt_template)
            template = template_path.read_text(encoding="utf-8")
            base = template.format(role=self.card.role, role_description=self.card.role_description)
        return base + self._rules_section()

    def _rules_section(self) -> str:
        # Three tiers, broadest to narrowest, appended after the role
        # description rather than woven into it, so they read as explicit
        # standing instructions rather than part of the character the model
        # is asked to play: the global rulefile (every agent, every
        # survey), this survey's own rulefile (every agent in this one
        # survey), and this agent's own rulefile (this agent only).
        global_rules = app_config.load_global_rulefile().strip()
        survey_rulefile_path = self.storage.root / "rulefile.md"
        survey_rules = survey_rulefile_path.read_text(encoding="utf-8").strip() if survey_rulefile_path.exists() else ""
        agent_rules = self.card.rulefile.strip()
        parts = []
        if global_rules:
            parts.append(f"\n\n## Rules you must follow\n\n{global_rules}")
        if survey_rules:
            parts.append(f"\n\n## Rules for this survey\n\n{survey_rules}")
        if agent_rules:
            parts.append(f"\n\n## Additional rules for this agent\n\n{agent_rules}")
        return "".join(parts)

    def _qa_precheck_ground_truth(self) -> Dict[str, Any]:
        return qa_checks.build_precheck_ground_truth(
            agent_id=self.card.agent_id,
            role=self.card.role,
            provider=self.card.model.provider,
            model_name=self.card.model.name,
            has_dedicated_rag=bool(self._retriever),
            has_shared_knowledge_repo=bool(self._knowledge_repo_retriever),
            role_pack=self.card.role_pack if role_packs.get_role_pack_text(self.card.role_pack) else None,
            has_web_search="web_search" in self.card.tools,
        )

    def _qa_precheck_prompt(self, ground_truth: Dict[str, Any], survey_title: str, survey_description: str) -> str:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        display = self.card.display_name or self.card.role
        project_line = survey_title if not survey_description else f"{survey_title}: {survey_description}"
        caps = ground_truth["capabilities"]
        return (
            "Before starting the actual survey task, confirm your configuration so a human "
            "reviewer can verify you understood it correctly, rather than assuming you did.\n\n"
            f"You are agent ID \"{ground_truth['agent_id']}\", display name \"{display}\", role "
            f"\"{ground_truth['role']}\", running as model \"{ground_truth['model']}\". The current "
            f"date and time is {now}. The project you are working on is \"{project_line}\".\n\n"
            "For this survey you have been granted exactly these capabilities: "
            f"dedicated RAG corpus: {caps['dedicated_rag_corpus']}. Shared survey knowledge "
            f"repository: {caps['shared_knowledge_repo']}. Standard role knowledge pack: "
            f"{caps['role_pack'] or 'none'}. Web search: {caps['web_search']}.\n\n"
            "Respond with ONLY a JSON object, no other text, in exactly this shape, restating the "
            "configuration above accurately. Do not add any capability or knowledge source beyond "
            "what was just stated, and do not answer the actual survey questions yet: this turn "
            "is only your configuration check.\n"
            "{\n"
            '  "agent_id": "<copy exactly>",\n'
            '  "role": "<copy exactly>",\n'
            '  "model": "<copy exactly, provider/name>",\n'
            '  "capabilities": {\n'
            '    "dedicated_rag_corpus": <true or false>,\n'
            '    "shared_knowledge_repo": <true or false>,\n'
            '    "role_pack": "<pack name, or null if none>",\n'
            '    "web_search": <true or false>\n'
            "  },\n"
            '  "acknowledgement": "<1-2 sentences confirming you understand the assignment and '
            'will attempt it as an expert in your role>"\n'
            "}"
        )

    def run_qa_precheck(self, survey_title: str, survey_description: str = "") -> None:
        """A single, un-repeated preliminary turn: the agent is told its
        real, actual configuration and asked to restate it, and that
        restatement is verified against ground truth deterministically (see
        qa_checks.py), not merely trusted. A mismatch (a hallucinated
        capability, or a comprehension failure) is logged plainly, not
        hidden, so a human reviewer can see it before trusting this agent's
        actual answers. Logged as this agent's second conversation-trace
        entry: `orchestrator.py` already logs a `spawn_declared` entry (see
        `spawning/spawn.py::declare_root`) before this agent is even
        constructed, so the precheck is the first entry the agent itself is
        responsible for, not the trace's absolute first entry."""
        ground_truth = self._qa_precheck_ground_truth()
        provider = get_provider(self.card.model.provider)
        messages = [
            {"role": "system", "content": self._role_description()},
            {"role": "user", "content": self._qa_precheck_prompt(ground_truth, survey_title, survey_description)},
        ]
        response = provider.complete(
            messages,
            model=self.card.model.name,
            temperature=self.card.model.temperature,
            max_tokens=min(self.card.model.max_tokens, 512),
            top_p=self.card.model.top_p,
            seed=self.card.model.seed,
        )
        claimed = _extract_json_object(response.text)
        verification = qa_checks.verify_precheck_response(claimed, ground_truth)
        self.storage.write_qa_precheck(self.card.agent_id, ground_truth, response, claimed, verification)

    def _context_chunks(self, query: str) -> List[str]:
        return (
            self._role_pack_chunks()
            + self._rag_chunks(query)
            + self._knowledge_repo_chunks(query)
            + self._web_search_chunks(query)
        )

    def _role_pack_chunks(self) -> List[str]:
        # A standard role knowledge pack is a fixed professional-domain
        # primer (see role_packs/), not something retrieved by relevance.
        # It is included in full, every run, exactly like a human panelist
        # in that role would already know this material going in, rather
        # than looking it up per question.
        text = role_packs.get_role_pack_text(self.card.role_pack)
        if not text:
            return []
        self.storage.write_tool_call(
            self.card.agent_id,
            tool="role_pack",
            detail={"role_pack": self.card.role_pack},
        )
        return [f"[role knowledge: {self.card.role_pack}] {text}"]

    def _rag_chunks(self, query: str) -> List[str]:
        if not self._retriever:
            return []
        chunks = self._retriever.top_k(query, self.card.rag.top_k)
        self.storage.write_tool_call(
            self.card.agent_id,
            tool="rag_retrieval",
            detail={
                "corpus_path": self.card.rag.corpus_path,
                "query": query,
                "top_k": self.card.rag.top_k,
                "retrieved_sources": [c.source for c in chunks],
            },
        )
        return [f"[{c.source}] {c.text}" for c in chunks]

    def _knowledge_repo_chunks(self, query: str) -> List[str]:
        if not self._knowledge_repo_retriever:
            return []
        top_k = app_config.rag_defaults().get("top_k", 5)
        chunks = self._knowledge_repo_retriever.top_k(query, top_k)
        self.storage.write_tool_call(
            self.card.agent_id,
            tool="knowledge_repo_retrieval",
            detail={
                "corpus_path": f"{KNOWLEDGE_REPO_DIRNAME}/ (shared, survey-level)",
                "query": query,
                "top_k": top_k,
                "retrieved_sources": [c.source for c in chunks],
            },
        )
        return [f"[shared knowledge: {c.source}] {c.text}" for c in chunks]

    def _web_search_chunks(self, query: str) -> List[str]:
        if "web_search" not in self.card.tools:
            return []
        try:
            results = search_as_dicts(query, top_k=5)
        except WebSearchError as exc:
            # An optional grounding tool being unavailable (no API key,
            # network failure) does not fail the agent: it proceeds with
            # whatever other context it has, exactly like a RAG corpus
            # that happens to retrieve nothing. The failure is logged, not
            # hidden, so a reviewer can see the agent never actually got
            # to search rather than assuming it did.
            self.storage.write_tool_call(
                self.card.agent_id, tool="web_search", detail={"query": query, "error": str(exc)}
            )
            return []
        self.storage.write_tool_call(
            self.card.agent_id,
            tool="web_search",
            detail={"query": query, "results": results},
        )
        return [f"[web: {r['title']} ({r['url']})] {r['content']}" for r in results]

    def run(
        self,
        instrument: Instrument,
        instrument_params: Dict[str, Any],
        survey_title: str = "",
        survey_description: str = "",
    ) -> GuardedRun:
        # Manual-provider agents skip the automated QA precheck: a human is
        # already pasting every one of that agent's responses by hand, so an
        # automated self-verification call has no model to call.
        if self.card.model.provider != "manual":
            self.run_qa_precheck(survey_title, survey_description)

        role_description = self._role_description()
        # Same derived query drives every context source (dedicated RAG,
        # the survey's shared knowledge repo, and web search): role plus
        # the criteria being weighed is the one query that's actually
        # available before the model has said anything.
        query_for_context = f"{self.card.role}: {instrument_params.get('dimensions', [])}"
        context_chunks = self._context_chunks(query_for_context)

        messages = instrument.build_messages(role_description, context_chunks, instrument_params)
        self.storage.write_prompt(self.card.agent_id, messages)
        provider = get_provider(self.card.model.provider)

        extra_call_kwargs = None
        if self.card.model.provider == "manual":
            extra_call_kwargs = {"manual_dir": str(self.storage.agent_dir(self.card.agent_id) / "manual_input")}

        run = run_with_guardrails(
            provider,
            instrument,
            messages,
            instrument_params,
            model=self.card.model.name,
            temperature=self.card.model.temperature,
            max_tokens=self.card.model.max_tokens,
            top_p=self.card.model.top_p,
            seed=self.card.model.seed,
            repeats=self.card.sampling.repeats,
            max_retries_on_malformed=self.card.sampling.max_retries_on_malformed,
            agreement_threshold=self.card.sampling.agreement_threshold,
            denylist_patterns=self.card.guardrails.denylist_patterns,
            extra_call_kwargs=extra_call_kwargs,
        )
        self.storage.write_guarded_run(
            self.card.agent_id, run, card=self.card, instrument_params=instrument_params, context_chunks=context_chunks
        )
        return run
