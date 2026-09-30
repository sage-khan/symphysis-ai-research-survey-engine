"""Claude Code CLI provider: drives the locally-installed, already-authenticated
`claude` binary as a one-shot completion backend, instead of the Anthropic API
(anthropic_provider.py, which requires a separate ANTHROPIC_API_KEY). This is
the mechanism behind Phase 3 of the TrustRouter agentic BWM panel (Haiku/
Sonnet/Opus agents) -- see agentic-experiment-design-decisions.md's Phase 3
entry (project-veritas) for why: the machine already has a logged-in `claude`
CLI session (a subscription, not per-token API billing), and the survey
pipeline's existing provider abstraction (base.py's LLMProvider protocol) is
architecture-agnostic about how a completion is actually produced, so a
subprocess call is a drop-in fourth kind of provider alongside ollama/
anthropic/openai-compatible.

Each call is a brand-new, isolated `claude -p` process: no conversation state,
no cross-call prompt-cache reuse (confirmed by measurement: every invocation
pays a fixed ~11K-token cache_creation overhead for Claude Code's own tool/
environment context, even under --restricted with a fully custom
--system-prompt). This is real, non-trivial cost per call (measured floor:
Haiku ~$0.024, Sonnet ~$0.060, Opus ~$0.120 for a near-empty prompt) --
accepted here as the tradeoff for reusing the existing subscription rather
than requiring a separate ANTHROPIC_API_KEY, per Dan's explicit choice to run
this on-machine via the Claude Code CLI. See the design-decisions doc for the
full scope discussion (Haiku+Sonnet only, Opus dropped after seeing the cost
estimate).

--restricted (strips Bash/PowerShell/REPL/WebFetch) plus a fully custom
--system-prompt (replacing Claude Code's own default) keep each call to a
plain text-in/text-out completion with no tool use, no filesystem access
beyond the process's own cwd, and no risk of the model wandering into
exploring this repository instead of answering the survey question.
--disallowedTools additionally removes Read/Glob/Grep specifically (see the
thinking-budget paragraph below for why this pairing matters, not just
--restricted alone).

temperature/top_p/seed are accepted (the LLMProvider protocol requires them)
but silently unused: the `claude` CLI exposes no flag for any of the three,
unlike the raw Anthropic API. This project's Claude-tier agent cards should
not rely on deterministic seeding; repeats=3 sampling variance is the
existing mechanism for capturing response spread regardless of provider.

Extended-thinking budget is capped via MAX_THINKING_TOKENS, not left at the
CLI's own default. Found live running the Phase 3 pilot (2026-09-02, see
agentic-experiment-design-decisions.md): a real RAG-grounded survey prompt
(~15K chars of inline reference material) drove Haiku's default thinking
budget to ~9,600-12,000 tokens per call -- 97%+ of its total output --
pushing per-call wall time to 80-120s and cost to ~$0.07-0.08, roughly 10x
the near-empty-prompt floor measured earlier. Setting MAX_THINKING_TOKENS=0
"fixed" the latency (16s) but broke correctness: without any deliberation
budget, the model reflexively tried to Read() the reference material as a
file, named after the [tag] label it was given inline (e.g.
"blockchain_trust_and_attack_resistance.md"), found no such file in the
empty scratch cwd, and answered "the reference material file is not
accessible" instead of using the material actually pasted in its own
prompt. A moderate cap (MAX_THINKING_TOKENS=2000) plus explicitly
disallowing the Read/Glob/Grep tools (so there is no file-lookup reflex left
to trigger even if the model is tempted to reach for one) resolved both
problems together: ~17-19s per call, ~$0.02-0.035, and correct, substantive,
schema-valid answers grounded in the inline material every time tested.
2000 is an empirically-chosen balance for this task's actual complexity (a
single BWM comparison, not a multi-step coding problem), not a documented
Anthropic default -- revisit if a future task needs deeper reasoning.

The full extended-thinking trace is captured, not discarded: `--output-
format json` (a single result object) has no field for it at all, so this
provider uses `--output-format stream-json --verbose` instead and parses
the streamed per-message JSON lines for `type: "assistant"` messages whose
`content` contains a `{"type": "thinking", "thinking": "<text>"}` block.
That text is placed at `raw["message"]["thinking"]` on the returned
ProviderResponse -- the exact shape `audit/logger.py::_extract_thinking()`
already looks for (built for Ollama's deepseek-r1/qwen3-style
`message.thinking` field) -- so the existing pipeline surfaces it into
each sample's `sample_NN.md` ("Full reasoning trace") and the agent's
`thoughts.md` automatically, with no further plumbing changes needed. Dan
asked for this explicitly (2026-09-02): the survey's own `reasoning` field
is the model's own after-the-fact SUMMARY of its reasoning, submitted
alongside its answer; the captured thinking block is the actual internal
deliberation that produced it, and the two are not the same text.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List

from .base import ProviderError, ProviderResponse

_MODEL_ALIASES = {"haiku", "sonnet", "opus", "fable"}
_DEFAULT_MAX_THINKING_TOKENS = "2000"


class ClaudeCliProvider:
    def __init__(self, binary: str = "claude", timeout_s: int = 300, max_thinking_tokens: str = _DEFAULT_MAX_THINKING_TOKENS) -> None:
        self.binary = shutil.which(binary) or binary
        self.timeout_s = timeout_s
        self.max_thinking_tokens = max_thinking_tokens
        if shutil.which(binary) is None:
            raise ProviderError(f"'{binary}' CLI not found on PATH")

    def complete(
        self,
        messages: List[Dict[str, str]],
        *,
        model: str,
        temperature: float,
        max_tokens: int,
        top_p: float = 1.0,
        seed: int | None = None,
        **extra: Any,
    ) -> ProviderResponse:
        if model not in _MODEL_ALIASES:
            raise ProviderError(
                f"model={model!r} is not a recognized `claude` CLI alias; expected one of {sorted(_MODEL_ALIASES)}"
            )

        system_parts = [m["content"] for m in messages if m["role"] == "system"]
        user_parts = [m["content"] for m in messages if m["role"] != "system"]
        if not user_parts:
            raise ProviderError("ClaudeCliProvider requires at least one non-system message")

        system_prompt = "\n\n".join(system_parts) or "You are a helpful assistant."
        user_prompt = "\n\n".join(user_parts)

        # Run from an isolated empty scratch directory, never this repo's own
        # working directory: --restricted already removes the tools that
        # could read/write files, but there is no reason for the process's
        # cwd (visible to the model via its own environment-info block) to
        # be a real project directory at all for a plain text-completion task.
        with tempfile.TemporaryDirectory(prefix="claude_cli_provider_") as scratch:
            cmd = [
                self.binary,
                "-p",
                user_prompt,
                "--model",
                model,
                "--restricted",
                "--disallowedTools",
                "Read,Glob,Grep",
                "--system-prompt",
                system_prompt,
                "--output-format",
                "stream-json",
                "--verbose",
            ]
            env = dict(os.environ)
            env["MAX_THINKING_TOKENS"] = self.max_thinking_tokens
            try:
                proc = subprocess.run(
                    cmd,
                    cwd=scratch,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_s,
                    env=env,
                )
            except subprocess.TimeoutExpired as exc:
                raise ProviderError(f"claude CLI timed out after {self.timeout_s}s") from exc

            stdout = proc.stdout.strip()
            if not stdout:
                raise ProviderError(
                    f"claude CLI produced no stdout (exit={proc.returncode}): {proc.stderr[:2000]}"
                )

            thinking_parts: List[str] = []
            result_payload: Dict[str, Any] | None = None
            for line in stdout.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue  # a non-JSON stray line should never abort an otherwise-valid stream
                if event.get("type") == "assistant":
                    for block in event.get("message", {}).get("content", []):
                        if block.get("type") == "thinking" and block.get("thinking"):
                            thinking_parts.append(block["thinking"])
                elif event.get("type") == "result":
                    result_payload = event

            if result_payload is None:
                raise ProviderError(f"claude CLI stream had no terminal 'result' event: {stdout[:2000]}")

            if result_payload.get("is_error"):
                raise ProviderError(f"claude CLI reported an error: {result_payload.get('result', result_payload)}")

            text = result_payload.get("result", "")
            if not text:
                raise ProviderError(f"claude CLI returned an empty 'result' field: {result_payload}")

            raw = dict(result_payload)
            raw["message"] = {"thinking": "\n\n---\n\n".join(thinking_parts)} if thinking_parts else {}

            return ProviderResponse(
                text=text,
                raw=raw,
                model=model,
                finish_reason=result_payload.get("subtype", ""),
            )
