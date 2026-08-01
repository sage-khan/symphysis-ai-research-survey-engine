"""Anti-hallucination / structural guardrails applied to every agent call.

Three checks, all logged: (1) schema validation with reject-and-resample on
malformed output, (2) repeated independent sampling per agent so a point
estimate is never taken from a single completion, (3) an optional
inter-sample agreement check that flags (not silently drops) high-variance
agents for human review.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List

from .instruments.base import Instrument, InstrumentResult
from .providers.base import LLMProvider, ProviderResponse


@dataclass
class GuardedRun:
    accepted: List[InstrumentResult]
    rejected: List[Dict[str, Any]]  # {"raw_text": ..., "errors": [...], "attempt": n}
    raw_completions: List[ProviderResponse]  # every completion, accepted or not, for the audit log
    flagged_low_agreement: bool = False


def run_with_guardrails(
    provider: LLMProvider,
    instrument: Instrument,
    messages: List[Dict[str, str]],
    instrument_params: Dict[str, Any],
    *,
    model: str,
    temperature: float,
    max_tokens: int,
    top_p: float,
    seed: int | None,
    repeats: int,
    max_retries_on_malformed: int,
    agreement_threshold: float,
    agreement_fn: Callable[[List[InstrumentResult]], float] | None = None,
) -> GuardedRun:
    accepted: List[InstrumentResult] = []
    rejected: List[Dict[str, Any]] = []
    raw_completions: List[ProviderResponse] = []

    for sample_idx in range(repeats):
        attempt = 0
        while attempt <= max_retries_on_malformed:
            response = provider.complete(
                messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                seed=(seed + sample_idx if seed is not None else None),
            )
            raw_completions.append(response)
            result = instrument.parse(response.text, instrument_params)
            if result.valid:
                accepted.append(result)
                break
            rejected.append({"raw_text": response.text, "errors": result.errors, "attempt": attempt})
            attempt += 1
        # If all retries for this sample were malformed, it is recorded in
        # `rejected` and simply does not contribute a sample; it is never
        # silently invented or filled in.

    flagged = False
    if agreement_threshold > 0 and agreement_fn is not None and len(accepted) > 1:
        agreement = agreement_fn(accepted)
        flagged = agreement < agreement_threshold

    return GuardedRun(accepted=accepted, rejected=rejected, raw_completions=raw_completions, flagged_low_agreement=flagged)
