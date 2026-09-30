"""Tests for runtime/openmanus.py. The AgentCard.model -> LLMSettings
mapping and isolated_venv_ready() are pure/fast and always run. The actual
subprocess smoke test (test_spawn_and_stream_events_against_isolated_venv)
only runs if vendor/openmanus/.venv exists (see
docs/architecture/governance-layer-and-runtime-backends-plan.md's
"isolated venv" setup step) — it is skipped, not failed, when that venv
hasn't been set up, so this file stays green on a machine that never
opted into building it."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest

from symphysis.runtime import openmanus as openmanus_runtime
from symphysis.runtime.base import TaskSpec


def test_module_imports_without_openmanus_dependencies():
    # If this test file collected and this assertion runs at all, the import
    # at the top of this file already succeeded without vendor/openmanus's
    # deps installed in THIS interpreter (the pymc/pytensor conda env pytest
    # runs under) — that is the property under test. OpenManus's own deps
    # live only in vendor/openmanus/.venv, never here.
    assert hasattr(openmanus_runtime, "OpenManusBackend")


def test_to_llm_settings_ollama():
    settings = openmanus_runtime.to_llm_settings(
        provider="ollama", model_name="qwen2.5:14b", temperature=0.7, max_tokens=1024
    )
    assert settings["base_url"] == "http://localhost:11434/v1"
    assert settings["api_type"] == "ollama"
    assert settings["model"] == "qwen2.5:14b"
    assert settings["temperature"] == 0.7
    assert settings["max_tokens"] == 1024
    assert settings["api_key"]  # non-empty placeholder, required by LLMSettings


def test_to_llm_settings_ollama_respects_env_base_url(monkeypatch):
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://veritas.tail4061d3.ts.net:11434")
    settings = openmanus_runtime.to_llm_settings(
        provider="ollama", model_name="qwen2.5:14b", temperature=0.7, max_tokens=1024
    )
    assert settings["base_url"] == "http://veritas.tail4061d3.ts.net:11434/v1"


def test_to_llm_settings_openai_compatible_provider_uses_known_fallback_base_url():
    settings = openmanus_runtime.to_llm_settings(
        provider="groq", model_name="llama-3.3-70b-versatile", temperature=0.2, max_tokens=2048
    )
    assert settings["base_url"] == "https://api.groq.com/openai/v1"
    assert settings["api_type"] == "openai"


def test_to_llm_settings_rejects_anthropic():
    with pytest.raises(ValueError, match="cannot route provider='anthropic'"):
        openmanus_runtime.to_llm_settings(
            provider="anthropic", model_name="claude-opus-5", temperature=0.7, max_tokens=1024
        )


def test_to_llm_settings_rejects_manual():
    with pytest.raises(ValueError, match="cannot route provider='manual'"):
        openmanus_runtime.to_llm_settings(provider="manual", model_name="", temperature=0.7, max_tokens=1024)


def test_spawn_raises_actionable_error_when_isolated_venv_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(openmanus_runtime, "_ISOLATED_VENV_PYTHON", tmp_path / "does-not-exist" / "python")
    backend = openmanus_runtime.OpenManusBackend()
    task = TaskSpec(
        agent_id="a1",
        did="did:key:z6Mktest",
        messages=[{"role": "user", "content": "hi"}],
        model_provider="ollama",
        model_name="qwen2.5:14b",
        temperature=0.7,
        max_tokens=1024,
    )
    with pytest.raises(FileNotFoundError, match="uv venv"):
        backend.spawn(task)


@pytest.mark.skipif(
    not openmanus_runtime.isolated_venv_ready(),
    reason="vendor/openmanus/.venv not set up; see the plan doc's isolated-venv setup step",
)
def test_spawn_and_stream_events_against_isolated_venv():
    """A real smoke test against the isolated venv's python interpreter and
    the actual vendored OpenManus source — not a mock. It deliberately does
    NOT talk to a real Ollama server or model: instead it points the agent's
    OpenAI-compatible client at a bogus port, so the assertion is that the
    driver subprocess starts, imports OpenManus cleanly, attempts the LLM
    call, and reports the resulting connection failure back as a
    same-process "error" event over the JSON contract — proving the
    subprocess/venv/import/streaming plumbing genuinely works end-to-end,
    without requiring a live model server in the test environment.

    Runs ~25-30s, not instant: vendor/openmanus/app/llm.py's LLM.ask/ask_tool
    are @retry-wrapped (tenacity, wait_random_exponential(min=1, max=60),
    stop_after_attempt(6)) and retry on almost any exception, including a
    plain connection refusal — a genuine failure only surfaces after all 6
    attempts exhaust. This is real OpenManus behavior, not a driver bug: a
    production OpenManus-backed agent hitting an unreachable model endpoint
    will retry for tens of seconds before Symphysis's orchestrator sees the
    failure (see the plan doc's Phase 2 implementation notes)."""
    backend = openmanus_runtime.OpenManusBackend()
    task = TaskSpec(
        agent_id="smoke-agent",
        did="did:key:z6MkSmokeTest",
        messages=[{"role": "user", "content": "Say hello."}],
        model_provider="ollama",
        model_name="qwen2.5:14b",
        temperature=0.7,
        max_tokens=64,
        extra={"max_steps": 1},
    )
    import os

    old = os.environ.get("OLLAMA_BASE_URL")
    os.environ["OLLAMA_BASE_URL"] = "http://127.0.0.1:1"  # nothing listens here
    try:
        handle = backend.spawn(task)
    finally:
        if old is None:
            os.environ.pop("OLLAMA_BASE_URL", None)
        else:
            os.environ["OLLAMA_BASE_URL"] = old

    events = list(backend.stream_events(handle))
    assert len(events) >= 1
    assert events[-1].kind == "error"
    message = events[-1].payload.get("message", "")
    # A genuine connection failure surfaced through tenacity's RetryError,
    # not a driver-side crash (e.g. the AttributeError from the earlier
    # bare-LLMSettings construction bug, or the DaytonaSettings ValidationError
    # from missing vendor/openmanus/config/config.toml — both fixed upstream
    # of this test; a regression in either would change this message).
    assert "RetryError" in message or "APIConnectionError" in message, message


class _FakeBackend:
    """Stands in for OpenManusBackend so OpenManusProvider.complete() is
    unit-tested without a real subprocess/venv, matching this test suite's
    existing _FakeProvider-at-the-boundary pattern (see test_qa_precheck.py)."""

    def __init__(self, events):
        self._events = events
        self.spawned_tasks = []

    def spawn(self, task):
        self.spawned_tasks.append(task)
        return object()

    def stream_events(self, handle):
        yield from self._events


def test_openmanus_provider_complete_returns_provider_response_from_final_event():
    from symphysis.runtime.base import Event
    from symphysis.runtime.openmanus import OpenManusProvider

    provider = OpenManusProvider(model_provider="ollama", agent_id="a1", did="did:key:z6Mktest")
    provider._backend = _FakeBackend(
        [
            Event(kind="thought", payload={"step": 1, "result": "thinking..."}),
            Event(kind="raw_completion", payload={"response": {"text": "final answer", "model": "qwen2.5:14b", "finish_reason": "stop"}}),
        ]
    )

    response = provider.complete(
        [{"role": "user", "content": "hi"}], model="qwen2.5:14b", temperature=0.7, max_tokens=512
    )
    assert response.text == "final answer"
    assert response.finish_reason == "stop"
    assert provider._backend.spawned_tasks[0].model_name == "qwen2.5:14b"


def test_openmanus_provider_complete_raises_on_error_event():
    from symphysis.runtime.base import Event
    from symphysis.runtime.openmanus import OpenManusProvider, OpenManusProviderError

    provider = OpenManusProvider(model_provider="ollama", agent_id="a1", did="did:key:z6Mktest")
    provider._backend = _FakeBackend([Event(kind="error", payload={"message": "boom"})])

    with pytest.raises(OpenManusProviderError, match="boom"):
        provider.complete([{"role": "user", "content": "hi"}], model="qwen2.5:14b", temperature=0.7, max_tokens=512)


def test_openmanus_provider_complete_raises_when_no_events_at_all():
    from symphysis.runtime.openmanus import OpenManusProvider, OpenManusProviderError

    provider = OpenManusProvider(model_provider="ollama", agent_id="a1", did="did:key:z6Mktest")
    provider._backend = _FakeBackend([])

    with pytest.raises(OpenManusProviderError, match="no completion event"):
        provider.complete([{"role": "user", "content": "hi"}], model="qwen2.5:14b", temperature=0.7, max_tokens=512)


def test_openmanus_provider_complete_threads_survey_panel_extra_through_to_the_task(monkeypatch):
    # Phase 3 (plan doc tasks 17-19): Agent.run() passes flow/levels/
    # level_messages through complete()'s **extra; this is the boundary
    # test proving OpenManusProvider forwards them into TaskSpec.extra
    # unchanged, without needing a real subprocess.
    from symphysis.runtime.base import Event
    from symphysis.runtime.openmanus import OpenManusProvider

    provider = OpenManusProvider(model_provider="ollama", agent_id="a1", did="did:key:z6Mktest")
    provider._backend = _FakeBackend(
        [Event(kind="raw_completion", payload={"response": {"text": "{}", "model": "qwen2.5:14b", "finish_reason": "stop"}})]
    )
    levels = [{"id": "L1", "dimensions": ["A", "B"]}]
    level_messages = {"L1": [{"role": "user", "content": "answer L1"}]}

    provider.complete(
        [{"role": "user", "content": "hi"}],
        model="qwen2.5:14b",
        temperature=0.7,
        max_tokens=512,
        flow="survey_panel",
        levels=levels,
        level_messages=level_messages,
    )

    task = provider._backend.spawned_tasks[0]
    assert task.extra["flow"] == "survey_panel"
    assert task.extra["levels"] == levels
    assert task.extra["level_messages"] == level_messages


def test_openmanus_provider_complete_ignores_flow_extra_when_not_survey_panel():
    from symphysis.runtime.base import Event
    from symphysis.runtime.openmanus import OpenManusProvider

    provider = OpenManusProvider(model_provider="ollama", agent_id="a1", did="did:key:z6Mktest")
    provider._backend = _FakeBackend(
        [Event(kind="raw_completion", payload={"response": {"text": "{}", "model": "qwen2.5:14b", "finish_reason": "stop"}})]
    )

    provider.complete([{"role": "user", "content": "hi"}], model="qwen2.5:14b", temperature=0.7, max_tokens=512)

    task = provider._backend.spawned_tasks[0]
    assert "flow" not in task.extra
    assert "levels" not in task.extra


def test_backend_spawn_writes_survey_panel_fields_into_the_driver_spec(tmp_path, monkeypatch):
    from symphysis.runtime import openmanus as openmanus_runtime
    from symphysis.runtime.base import TaskSpec

    monkeypatch.setattr(openmanus_runtime, "isolated_venv_ready", lambda: True)

    captured = {}

    class _FakePopen:
        def __init__(self, args, **kwargs):
            captured["input_path"] = Path(args[2])
            self.stdout = iter([])
            self.stderr = None

        def wait(self):
            return 0

    monkeypatch.setattr(openmanus_runtime.subprocess, "Popen", _FakePopen)

    backend = openmanus_runtime.OpenManusBackend()
    task = TaskSpec(
        agent_id="a1",
        did="did:key:z6Mktest",
        messages=[{"role": "user", "content": "hi"}],
        model_provider="ollama",
        model_name="qwen2.5:14b",
        temperature=0.7,
        max_tokens=512,
        extra={
            "flow": "survey_panel",
            "levels": [{"id": "L1", "dimensions": ["A", "B"]}],
            "level_messages": {"L1": [{"role": "user", "content": "answer L1"}]},
            "level_max_steps": 4,
        },
    )
    backend.spawn(task)

    spec = json.loads(captured["input_path"].read_text(encoding="utf-8"))
    assert spec["flow"] == "survey_panel"
    assert spec["levels"] == [{"id": "L1", "dimensions": ["A", "B"]}]
    assert spec["level_messages"] == {"L1": [{"role": "user", "content": "answer L1"}]}
    assert spec["level_max_steps"] == 4
