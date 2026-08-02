"""A single agent instance: identity (DID, from its Agent Card) + one
elicitation run, with permissions enforced from the same card."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from .agent_card import AgentCard
from .guardrails import GuardedRun, run_with_guardrails
from .instruments.base import Instrument
from .permissions import check_data_scope, check_provider_allowed
from .providers import get_provider
from .rag.retriever import build_retriever
from .storage import SurveyStorage


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

    def _role_description(self) -> str:
        if self.card.system_prompt_override:
            # Literal, user-edited text (e.g. from the web UI's Agent panel) --
            # not run through .format(), since free-typed text may contain
            # stray "{"/"}" that would raise on a template substitution never
            # intended to apply to it.
            return self.card.system_prompt_override
        template_path = Path(self.card.system_prompt_template)
        template = template_path.read_text(encoding="utf-8")
        return template.format(role=self.card.role, role_description=self.card.role_description)

    def _introduction_prompt(self, survey_title: str, survey_description: str) -> str:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        display = self.card.display_name or self.card.role
        project_line = survey_title if not survey_description else f"{survey_title} -- {survey_description}"
        return (
            "Before starting the task, introduce yourself in 2-4 sentences, in character, so a "
            "human reviewer can confirm you understood the assignment before you attempt it. "
            f"State clearly: your agent ID ({self.card.agent_id}), your display name ({display}), "
            f"your base model ({self.card.model.provider}/{self.card.model.name}), the current date "
            f"and time ({now}), the project you are working on ({project_line}), your role "
            f"({self.card.role}), and that you will attempt this task as an expert in that role. "
            "Do not answer the actual survey questions yet -- this turn is only your introduction."
        )

    def introduce(self, survey_title: str, survey_description: str = "") -> None:
        """A single, un-repeated preliminary turn logged as the first entry in
        this agent's conversation trace: the agent states its own identity and
        understanding of the task in plain language, so a human reviewer can
        see immediately whether the model understood the assignment, rather
        than only being able to infer that from terse per-sample reasoning."""
        provider = get_provider(self.card.model.provider)
        messages = [
            {"role": "system", "content": self._role_description()},
            {"role": "user", "content": self._introduction_prompt(survey_title, survey_description)},
        ]
        response = provider.complete(
            messages,
            model=self.card.model.name,
            temperature=self.card.model.temperature,
            max_tokens=min(self.card.model.max_tokens, 512),
            top_p=self.card.model.top_p,
            seed=self.card.model.seed,
        )
        self.storage.write_introduction(self.card.agent_id, response)

    def _context_chunks(self, query: str) -> List[str]:
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

    def run(
        self,
        instrument: Instrument,
        instrument_params: Dict[str, Any],
        survey_title: str = "",
        survey_description: str = "",
    ) -> GuardedRun:
        # Manual-provider agents skip the automated introduction: a human is
        # already pasting every one of that agent's responses by hand, so an
        # automated self-introduction call has no model to call.
        if self.card.model.provider != "manual":
            self.introduce(survey_title, survey_description)

        role_description = self._role_description()
        query_for_rag = f"{self.card.role}: {instrument_params.get('dimensions', [])}"
        context_chunks = self._context_chunks(query_for_rag)

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
        self.storage.write_guarded_run(self.card.agent_id, run, card=self.card, instrument_params=instrument_params)
        return run
