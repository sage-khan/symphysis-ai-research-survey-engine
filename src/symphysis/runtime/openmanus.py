"""The flagship, multi-turn/tool-using RuntimeBackend, driving a vendored,
pinned OpenManus install as an isolated subprocess.

Per docs/architecture/governance-layer-and-runtime-backends-plan.md Phase 2
(tasks 13-14). OpenManus itself lives at vendor/openmanus/ as a git
submodule pinned to commit 3309bf4e416fb1c74b008f3e86494439a31bad53
(FoundationAgents/OpenManus, MIT-licensed) — it is a pinned dependency, not
vendored/modified source: nothing in this repo edits anything under
vendor/openmanus/.

**Isolated venv, not an in-process import.** OpenManus's requirements.txt
pins pydantic~=2.10.6 and pulls in ~30 packages (browsergym, playwright,
docker, boto3, crawl4ai, ...), several version-pinned. Symphysis's own test
suite already runs pymc/pytensor for the Bayesian BWM solver in the same
conda environment; installing OpenManus's pins there risked a real
dependency conflict against the 229 tests that were already green before
this backend existed. So OpenManus runs in a fully separate Python
interpreter (`vendor/openmanus/.venv`, python3.12, built with `uv venv` +
`uv pip install -r requirements.txt` there, never into the main env this
package's own tests run under), driven as a subprocess via
`_openmanus_driver.py`. That script is deliberately the ONLY place in this
codebase that imports OpenManus's `app.*` package; this module never does.

This module is split into two independently-testable pieces:

1. `to_llm_settings(...)` — a pure function with no OpenManus import and no
   subprocess, so the AgentCard.model -> OpenManus LLMSettings mapping is
   fully unit-testable (see tests/test_runtime_openmanus.py) regardless of
   whether vendor/openmanus/.venv exists yet.
2. `OpenManusBackend` — launches `_openmanus_driver.py` under
   vendor/openmanus/.venv/bin/python and streams its NDJSON stdout back as
   `Event`s, satisfying the same `RuntimeBackend` protocol as
   `runtime/ollama.py`.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterator, Optional

from .. import app_config
from .base import Event, RunHandle, TaskSpec

_VENDOR_ROOT = Path(__file__).resolve().parents[3] / "vendor" / "openmanus"
_ISOLATED_VENV_PYTHON = _VENDOR_ROOT / ".venv" / "bin" / "python"
_DRIVER_SCRIPT = Path(__file__).with_name("_openmanus_driver.py")

# Providers this repo already knows how to reach over an OpenAI-compatible
# chat-completions endpoint. OpenManus's own LLM class (vendor/openmanus/app/llm.py)
# special-cases only "azure" and "aws" api_type; every other api_type value
# (including "ollama") falls through to a plain AsyncOpenAI(base_url=...)
# client, so any of these can share that same code path.
_OPENAI_COMPATIBLE = {
    "openai": ("OPENAI_API_KEY", None),
    "openrouter": ("OPENROUTER_API_KEY", "https://openrouter.ai/api/v1"),
    "groq": ("GROQ_API_KEY", "https://api.groq.com/openai/v1"),
    "gemini": ("GEMINI_API_KEY", "https://generativelanguage.googleapis.com/v1beta/openai/"),
    "xai": ("XAI_API_KEY", "https://api.x.ai/v1"),
}

# Providers this backend cannot currently route to OpenManus's LLM class:
# Anthropic's native API is not OpenAI-wire-compatible, and OpenManus's LLM
# class has no Anthropic client branch (only azure/aws/else-openai).
# "manual" (Symphysis's copy-paste-a-response provider) has no meaning for
# an autonomous multi-turn backend at all.
_UNSUPPORTED = {"anthropic", "manual"}


def to_llm_settings(
    *, provider: str, model_name: str, temperature: float, max_tokens: int
) -> Dict[str, Any]:
    """Pure mapping from a Symphysis ModelSpec's fields to the dict shape
    OpenManus's `app.config.LLMSettings` expects. Raises ValueError for a
    provider this backend cannot route (see _UNSUPPORTED above); callers
    should catch that and fall back to runtime/ollama.py's direct-completion
    backend for that agent instead of failing the whole survey.
    """
    if provider in _UNSUPPORTED:
        raise ValueError(
            f"runtime/openmanus.py cannot route provider={provider!r} to OpenManus's "
            "LLM class (no compatible client for it); use runtime/ollama.py "
            "(direct_completion) for this agent's card instead."
        )

    if provider == "ollama":
        base = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        return {
            "model": model_name,
            "base_url": f"{base.rstrip('/')}/v1",
            "api_key": "ollama",  # unused by Ollama's OpenAI-compat endpoint, but LLMSettings requires a non-empty str
            "max_tokens": max_tokens,
            "temperature": temperature,
            "api_type": "ollama",
            "api_version": "",
        }

    if provider in _OPENAI_COMPATIBLE:
        api_key_env, fallback_base_url = _OPENAI_COMPATIBLE[provider]
        base_url = app_config.provider_base_url(provider) or fallback_base_url
        if base_url is None:
            raise ValueError(
                f"No base_url configured for provider={provider!r} "
                f"(set provider_base_urls.{provider} in config, matching providers/openai_compatible.py)"
            )
        return {
            "model": model_name,
            "base_url": base_url,
            "api_key": os.environ.get(api_key_env, ""),
            "max_tokens": max_tokens,
            "temperature": temperature,
            "api_type": "openai",
            "api_version": "",
        }

    raise ValueError(f"Unknown provider {provider!r}; cannot map to OpenManus LLMSettings")


def isolated_venv_ready() -> bool:
    """True once vendor/openmanus/.venv exists with a python interpreter in
    it. Does not check that requirements.txt was actually installed there
    (that failure surfaces as an ImportError inside the subprocess instead,
    reported as an "error" event rather than silently)."""
    return _ISOLATED_VENV_PYTHON.exists()


class OpenManusHandle(RunHandle):
    def __init__(self, agent_id: str, process: subprocess.Popen, input_path: Path) -> None:
        super().__init__(agent_id=agent_id, backend_name="openmanus")
        self.process = process
        self.input_path = input_path


class OpenManusBackend:
    """RuntimeBackend that drives a SurveyElicitationAgent through
    OpenManus's own ReAct step loop inside an isolated subprocess (see
    module docstring). Requires vendor/openmanus/.venv to exist with
    OpenManus's dependencies installed; raises FileNotFoundError with an
    actionable message otherwise rather than failing obscurely."""

    name = "openmanus"

    def spawn(self, task: TaskSpec) -> RunHandle:
        if not isolated_venv_ready():
            raise FileNotFoundError(
                f"{_ISOLATED_VENV_PYTHON} not found. Set it up once with:\n"
                f"  cd {_VENDOR_ROOT} && uv venv --python 3.12 .venv && "
                f"uv pip install --python .venv/bin/python -r requirements.txt"
            )

        llm_settings = to_llm_settings(
            provider=task.model_provider,
            model_name=task.model_name,
            temperature=task.temperature,
            max_tokens=task.max_tokens,
        )
        spec = {
            "config_name": task.did,
            "llm_settings": llm_settings,
            "messages": task.messages,
            "max_steps": task.extra.get("max_steps", 15),
        }
        # Both optional: present only when the caller (OpenManusProvider,
        # see below) started a tools/proxy.py ToolProxyServer for this run.
        # See _openmanus_driver.py's module docstring for the full contract.
        if "proxy_port" in task.extra:
            spec["proxy_port"] = task.extra["proxy_port"]
        if "available_tools" in task.extra:
            spec["available_tools"] = task.extra["available_tools"]
        # Phase 3 (plan doc tasks 17-19): present only when Agent.run()
        # built a "survey_panel" call (a hierarchical instrument on an
        # openmanus-backend card, see agent.py::run()) — see
        # _openmanus_driver.py's module docstring for the full contract.
        if task.extra.get("flow") == "survey_panel":
            spec["flow"] = "survey_panel"
            spec["levels"] = task.extra["levels"]
            spec["level_messages"] = task.extra["level_messages"]
            if "level_max_steps" in task.extra:
                spec["level_max_steps"] = task.extra["level_max_steps"]
        # 2026-09-01: a flat (non-hierarchical) `bwm` instrument run through
        # OpenManus, answered as two plain non-tool-calling completions
        # instead of one tool-calling turn — see _openmanus_driver.py's
        # module docstring and _run_bwm_two_stage() for the full contract
        # and the design-decision log this fixes.
        if task.extra.get("flow") == "bwm_two_stage":
            spec["flow"] = "bwm_two_stage"
            spec["codes"] = task.extra["codes"]
            spec["labels"] = task.extra.get("labels", {})

        fd, input_path_str = tempfile.mkstemp(prefix=f"openmanus-{task.agent_id}-", suffix=".json")
        input_path = Path(input_path_str)
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(spec, fh)

        process = subprocess.Popen(
            [str(_ISOLATED_VENV_PYTHON), str(_DRIVER_SCRIPT), str(input_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # line-buffered, so NDJSON lines are readable as they're emitted
        )
        return OpenManusHandle(agent_id=task.agent_id, process=process, input_path=input_path)

    def stream_events(self, handle: RunHandle) -> Iterator[Event]:
        assert isinstance(handle, OpenManusHandle)
        try:
            saw_terminal_event = False
            for line in handle.process.stdout:
                line = line.strip()
                if not line:
                    continue
                parsed = json.loads(line)
                if parsed["kind"] in ("raw_completion", "error"):
                    saw_terminal_event = True
                yield Event(kind=parsed["kind"], payload=parsed["payload"])

            returncode = handle.process.wait()
            if returncode != 0 and not saw_terminal_event:
                stderr = handle.process.stderr.read() if handle.process.stderr else ""
                yield Event(
                    kind="error",
                    payload={"message": f"openmanus driver subprocess exited {returncode}: {stderr.strip()}"},
                )
        finally:
            handle.input_path.unlink(missing_ok=True)

    def stop(self, handle: RunHandle) -> None:
        assert isinstance(handle, OpenManusHandle)
        handle.process.terminate()


class OpenManusProviderError(Exception):
    """Raised when an OpenManus-backed run ends without a usable
    `raw_completion` event (an "error" event, or the stream ending with
    neither). Deliberately its own exception type, not `providers.base.ProviderError`,
    so a caller can tell "the model/network failed" (ProviderError) apart
    from "the OpenManus subprocess/ReAct loop itself failed" — but
    `Agent.run()` catches both alongside the same `except (ProviderError, ...)`
    handling already in `orchestrator.py`, since either way the practical
    behavior (skip this agent, log why, keep the panel going) is identical.
    """


class OpenManusProvider:
    """Satisfies `providers.base.LLMProvider`'s `complete(...)` interface by
    driving a `SurveyElicitationAgent` through `OpenManusBackend` instead of
    a single direct completion call. This is `Agent.run()`'s actual seam
    into Phase 2 (plan doc tasks 13-14): `guardrails.py::run_with_guardrails`
    already accepts any object exposing `.complete(...)`, so nothing
    downstream of `Agent.run()` (parsing, retries, solving, storage) needs
    to change, or even know, which backend produced the raw completion text.

    Known limitation, stated honestly rather than silently ignored:
    OpenManus's own `LLM` class (vendor/openmanus/app/llm.py) has no `seed`
    parameter on its chat-completion call, so a card's `model.seed` has no
    effect when `runtime_backend="openmanus"` — reproducibility for that
    agent then rests on `temperature`/prompt content alone, same as any
    provider/model combination that doesn't support seeding.

    `tools`/`storage`, when both given (see `Agent._resolve_provider()`),
    let the SurveyElicitationAgent make real, multi-turn RAG/web-search/
    citation-verify tool calls instead of relying solely on context baked
    into the prompt: a `tools/proxy.py::ToolProxyServer` is started for the
    duration of this one `complete()` call, and the subprocess is given its
    port plus each tool's JSON schema (plan doc Phase 2 tasks 15-16).
    Omitting them (the default) still works — the agent just has no tools
    beyond OpenManus's own baseline (CreateChatCompletion/Terminate).
    """

    def __init__(
        self,
        *,
        model_provider: str,
        agent_id: str,
        did: str,
        max_steps: int = 15,
        tools: Optional[Dict[str, Any]] = None,
        storage: Optional[Any] = None,
    ) -> None:
        self.model_provider = model_provider
        self.agent_id = agent_id
        self.did = did
        self.max_steps = max_steps
        self.tools = tools or {}
        self.storage = storage
        self._backend = OpenManusBackend()

    def complete(
        self,
        messages: Any,
        *,
        model: str,
        temperature: float,
        max_tokens: int,
        top_p: float = 1.0,
        seed: Optional[int] = None,
        **extra: Any,
    ) -> Any:
        from ..providers.base import ProviderResponse

        extra_task_fields: Dict[str, Any] = {"max_steps": self.max_steps}
        if extra.get("flow") == "survey_panel":
            extra_task_fields["flow"] = "survey_panel"
            extra_task_fields["levels"] = extra["levels"]
            extra_task_fields["level_messages"] = extra["level_messages"]
            if "level_max_steps" in extra:
                extra_task_fields["level_max_steps"] = extra["level_max_steps"]
        if extra.get("flow") == "bwm_two_stage":
            extra_task_fields["flow"] = "bwm_two_stage"
            extra_task_fields["codes"] = extra["codes"]
            extra_task_fields["labels"] = extra.get("labels", {})
        proxy_server = None
        if self.tools and self.storage is not None:
            from ..tools.proxy import ToolProxyServer

            proxy_server = ToolProxyServer(self.storage, self.agent_id, self.tools)
            proxy_server.start()
            extra_task_fields["proxy_port"] = proxy_server.port
            extra_task_fields["available_tools"] = [
                {"name": spec.name, "description": spec.description, "parameters": spec.parameters}
                for spec in self.tools.values()
            ]

        try:
            task = TaskSpec(
                agent_id=self.agent_id,
                did=self.did,
                messages=messages,
                model_provider=self.model_provider,
                model_name=model,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                seed=seed,
                extra=extra_task_fields,
            )
            handle = self._backend.spawn(task)
            final: Optional[Event] = None
            for event in self._backend.stream_events(handle):
                if event.kind in ("raw_completion", "error"):
                    final = event

            if final is None or final.kind == "error":
                message = (
                    (final.payload.get("message") if final else None) or "OpenManus run produced no completion event"
                )
                raise OpenManusProviderError(message)

            response = final.payload["response"]
            return ProviderResponse(
                text=response.get("text", ""),
                raw=response.get("raw", {}),
                model=response.get("model", model),
                finish_reason=response.get("finish_reason", ""),
            )
        finally:
            # The proxy server must outlive the entire subprocess run (it's
            # what makes the subprocess's tool calls work at all), so it is
            # only torn down after stream_events() has fully drained,
            # whether that ended in a normal raw_completion, an error event,
            # or an exception propagating out of this try block.
            if proxy_server is not None:
                proxy_server.stop()
