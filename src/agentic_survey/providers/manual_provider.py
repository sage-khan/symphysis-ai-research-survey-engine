"""Manual paste-in provider: for models with no API (e.g. the Gemini or GPT
web chat UI), a human copies the exact prompt into the chat, pastes the
reply back, and the pipeline consumes it exactly as it would any other
provider's completion, including through the same guardrails.

Two-step, resumable, per-agent workflow:
1. First call for a given manual_dir with no response file present: writes
   the exact outgoing prompt to `<manual_dir>/prompt_NN.md` and raises
   ManualResponsePending: a clear, actionable stop, not a crash.
2. Copy that prompt into the model's chat UI, paste the reply into
   `<manual_dir>/response_NN.txt`, and re-run. The agent picks up exactly
   where it left off; already-answered samples are not re-asked.

The sample index a given call is asking for is passed in explicitly by the
caller (guardrails.run_with_guardrails, as `sample_idx`) rather than
inferred from mutable state here. An earlier version inferred "the next
index" from a module-level call counter, which broke under a long-lived
server process: a counter that must reset exactly once per agent.run() call
happens to reset for free in a short-lived CLI process (the whole process
exits after each invocation) but does not reset between separate "run this
survey" clicks handled by the same long-running web-backend process. An
explicit, caller-supplied index has no such assumption to violate.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from .base import ProviderError, ProviderResponse


class ManualResponsePending(ProviderError):
    """Raised when a manual response is needed but hasn't been pasted yet.
    Not a failure of the pipeline: it's a stop-and-wait-for-a-human signal,
    logged and surfaced distinctly so it's never confused with a real
    provider outage."""


class ManualProvider:
    def complete(
        self,
        messages: List[Dict[str, str]],
        *,
        model: str,
        temperature: float,
        max_tokens: int,
        top_p: float = 1.0,
        seed: int | None = None,
        manual_dir: str | None = None,
        sample_idx: int | None = None,
        **extra: Any,
    ) -> ProviderResponse:
        if not manual_dir:
            raise ProviderError("ManualProvider requires manual_dir (set automatically for provider: manual agents)")
        if sample_idx is None:
            raise ProviderError("ManualProvider requires sample_idx (set automatically by run_with_guardrails)")

        d = Path(manual_dir)
        d.mkdir(parents=True, exist_ok=True)

        index = sample_idx
        prompt_path = d / f"prompt_{index:02d}.md"
        response_path = d / f"response_{index:02d}.txt"

        if not prompt_path.exists():
            prompt_path.write_text(_render_prompt(messages), encoding="utf-8")

        if not response_path.exists():
            raise ManualResponsePending(
                f"Paste {model}'s reply to {prompt_path} into {response_path}, then re-run. "
                f"(sample {index}; nothing was skipped or fabricated)"
            )

        text = response_path.read_text(encoding="utf-8")
        return ProviderResponse(text=text, raw={"manual_dir": str(d), "index": index}, model=model, finish_reason="manual")


def _render_prompt(messages: List[Dict[str, str]]) -> str:
    parts = ["# Paste this into the model's chat UI, then paste its reply into the matching response_NN.txt\n"]
    for msg in messages:
        parts.append(f"## {msg['role']}\n\n{msg['content']}\n")
    return "\n".join(parts)
