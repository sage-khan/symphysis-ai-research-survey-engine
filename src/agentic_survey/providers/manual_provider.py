"""Manual paste-in provider: for models with no API (e.g. the Gemini or GPT
web chat UI), a human copies the exact prompt into the chat, pastes the
reply back, and the pipeline consumes it exactly as it would any other
provider's completion, including through the same guardrails.

Two-step, resumable, per-agent workflow:
1. First call for a given manual_dir with no response file present: writes
   the exact outgoing prompt to `<manual_dir>/prompt_NN.md` and raises
   ManualResponsePending — a clear, actionable stop, not a crash.
2. Copy that prompt into the model's chat UI, paste the reply into
   `<manual_dir>/response_NN.txt`, and re-run. The agent picks up exactly
   where it left off; already-answered samples are not re-asked.

Within one process run, N sequential `complete()` calls for the same
manual_dir (one per requested sample) must visit index 0, 1, 2, ... in
order -- including a call immediately after a human has just pasted
sample 0's response, which must return sample 0's content, not skip ahead
to preparing sample 1. That requires an explicit per-directory call
counter; inferring "the next index" purely from which prompt/response
files already exist on disk cannot tell "return the answer I was just
given" apart from "move on to the next question" when both prompt and
response already exist for the current index.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from .base import ProviderError, ProviderResponse

_call_counters: Dict[str, int] = {}


class ManualResponsePending(ProviderError):
    """Raised when a manual response is needed but hasn't been pasted yet.
    Not a failure of the pipeline -- it's a stop-and-wait-for-a-human signal,
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
        **extra: Any,
    ) -> ProviderResponse:
        if not manual_dir:
            raise ProviderError("ManualProvider requires manual_dir (set automatically for provider: manual agents)")

        d = Path(manual_dir)
        d.mkdir(parents=True, exist_ok=True)

        key = str(d)
        index = _call_counters.get(key, 0)
        _call_counters[key] = index + 1

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
