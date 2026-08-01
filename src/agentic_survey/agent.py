"""A single agent instance: identity (DID) + config + one elicitation run."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from .config import AgentConfig
from .guardrails import GuardedRun, run_with_guardrails
from .instruments.base import Instrument
from .providers import get_provider
from .rag.retriever import build_retriever
from .storage import SurveyStorage


class Agent:
    def __init__(self, config: AgentConfig, storage: SurveyStorage) -> None:
        self.config = config
        self.storage = storage
        self.did = storage.init_agent(config.id, config.source_path)
        self._retriever = None
        if config.rag.enabled:
            self._retriever = build_retriever(
                config.rag.corpus_path, config.rag.chunk_size, config.rag.chunk_overlap, config.rag.embedding_model
            )

    def _role_description(self) -> str:
        template_path = Path(self.config.system_prompt_template)
        template = template_path.read_text(encoding="utf-8")
        return template.format(role=self.config.role, role_description=self.config.role_description)

    def _context_chunks(self, query: str) -> List[str]:
        if not self._retriever:
            return []
        chunks = self._retriever.top_k(query, self.config.rag.top_k)
        return [f"[{c.source}] {c.text}" for c in chunks]

    def run(self, instrument: Instrument, instrument_params: Dict[str, Any]) -> GuardedRun:
        role_description = self._role_description()
        query_for_rag = f"{self.config.role}: {instrument_params.get('dimensions', [])}"
        context_chunks = self._context_chunks(query_for_rag)

        messages = instrument.build_messages(role_description, context_chunks, instrument_params)
        provider = get_provider(self.config.model.provider)

        run = run_with_guardrails(
            provider,
            instrument,
            messages,
            instrument_params,
            model=self.config.model.name,
            temperature=self.config.model.temperature,
            max_tokens=self.config.model.max_tokens,
            top_p=self.config.model.top_p,
            seed=self.config.model.seed,
            repeats=self.config.sampling.repeats,
            max_retries_on_malformed=self.config.sampling.max_retries_on_malformed,
            agreement_threshold=self.config.sampling.agreement_threshold,
        )
        self.storage.write_guarded_run(self.config.id, run)
        return run
