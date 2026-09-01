"""Anti-hallucination / structural guardrails applied to every agent call.

Four checks, all logged: (1) schema validation with reject-and-repair on
malformed output, (2) a denylist regex scan of the raw completion (prompt-
injection markers, secret-shaped strings) applied before schema parsing, so
a response can be rejected even if it happens to also be well-formed JSON,
(3) repeated independent sampling per agent so a point estimate is never
taken from a single completion, (4) an optional inter-sample agreement
check that flags (not silently drops) high-variance agents for human
review.

Reject-and-repair, not reject-and-resample: a schema-invalid retry appends
the model's own malformed reply plus the exact validator errors as two new
turns, and asks for a corrected JSON object fixing only those problems.
Retrying with a fresh, independent prompt (the original behaviour) reuses
the same seed for every retry of one sample, so a model with a systematic
misunderstanding (see diagnostics.md's "hierarchical TrustRouter run was
zero_accepted" entry) produced the identical wrong answer on every retry
and never had a chance to correct it. Showing it the specific field-level
error targets the formatting/convention mistake without re-asking for a
fresh substantive judgement, which would defeat the point of `repeats`
sampling the same agent's honest variance across independent samples.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List

from .instruments.base import Instrument, InstrumentResult
from .providers.base import LLMProvider, ProviderResponse
from .providers.manual_provider import ManualResponsePending


@dataclass
class GuardedRun:
    accepted: List[InstrumentResult]
    rejected: List[Dict[str, Any]]  # {"raw_text": ..., "errors": [...], "attempt": n}
    raw_completions: List[ProviderResponse]  # every completion, accepted or not, for the audit log
    accepted_raw: List[ProviderResponse] = field(default_factory=list)  # same order/index as `accepted`; the exact raw completion that produced each one (so e.g. a reasoning model's "thinking" field can be shown alongside its parsed answer)
    flagged_low_agreement: bool = False
    pending_manual: str | None = None  # message to show the human, if a manual response is awaited


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
    denylist_patterns: List[str] | None = None,
    agreement_fn: Callable[[List[InstrumentResult]], float] | None = None,
    extra_call_kwargs: Dict[str, Any] | None = None,
) -> GuardedRun:
    accepted: List[InstrumentResult] = []
    accepted_raw: List[ProviderResponse] = []
    rejected: List[Dict[str, Any]] = []
    raw_completions: List[ProviderResponse] = []
    compiled_denylist = [re.compile(p, re.IGNORECASE) for p in (denylist_patterns or [])]
    pending_manual: str | None = None

    for sample_idx in range(repeats):
        # sample_idx is passed through to the provider (only when the caller
        # opted in via extra_call_kwargs, currently the manual provider) so
        # it can identify "which sample is this" itself, rather than
        # inferring it from mutable state. That state would otherwise need
        # to reset exactly once per agent.run() call and nowhere else, which
        # a short-lived CLI process gets for free but a long-lived server
        # process (this app's web UI) does not: the same provider instance
        # serves many separate "run this survey" clicks in one process.
        call_kwargs = dict(extra_call_kwargs) if extra_call_kwargs is not None else {}
        if extra_call_kwargs is not None:
            call_kwargs["sample_idx"] = sample_idx

        attempt = 0
        attempt_messages = list(messages)
        while attempt <= max_retries_on_malformed:
            if extra_call_kwargs is not None:
                call_kwargs["attempt"] = attempt
            try:
                response = provider.complete(
                    attempt_messages,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    top_p=top_p,
                    seed=(seed + sample_idx if seed is not None else None),
                    **call_kwargs,
                )
            except ManualResponsePending as exc:
                # Not a failure: a human hasn't pasted this sample's reply
                # yet. Stop asking for more samples from this agent (every
                # later index will be pending too) but let the rest of the
                # survey's agents keep running.
                pending_manual = str(exc)
                break
            raw_completions.append(response)

            denylist_hit = next((p.pattern for p in compiled_denylist if p.search(response.text)), None)
            if denylist_hit:
                rejected.append({
                    "raw_text": response.text,
                    "errors": [f"matched denylist pattern: {denylist_hit}"],
                    "attempt": attempt,
                })
                attempt += 1
                continue

            result = instrument.parse(response.text, instrument_params)
            if result.valid:
                accepted.append(result)
                accepted_raw.append(response)
                break
            rejected.append({"raw_text": response.text, "errors": result.errors, "attempt": attempt})
            if attempt < max_retries_on_malformed:
                attempt_messages = attempt_messages + [
                    {"role": "assistant", "content": response.text},
                    {
                        "role": "user",
                        "content": (
                            "That response did not pass validation. Problems found:\n"
                            + "\n".join(f"- {e}" for e in result.errors)
                            + "\n\nReturn a corrected JSON object that fixes only these "
                            "specific problems. Keep every other judgement (which "
                            "criterion is best/worst, and every other rating) exactly "
                            "as you gave it, unless fixing a listed problem requires "
                            "changing it. Respond with ONLY the corrected JSON object, "
                            "no other text."
                        ),
                    },
                ]
            attempt += 1
        # If all retries for this sample were malformed or denylisted, it is
        # recorded in `rejected` and simply does not contribute a sample; it
        # is never silently invented or filled in.
        if pending_manual:
            break

    flagged = False
    if agreement_threshold > 0 and agreement_fn is not None and len(accepted) > 1:
        agreement = agreement_fn(accepted)
        flagged = agreement < agreement_threshold

    return GuardedRun(
        accepted=accepted,
        accepted_raw=accepted_raw,
        rejected=rejected,
        raw_completions=raw_completions,
        flagged_low_agreement=flagged,
        pending_manual=pending_manual,
    )
