"""Tests for the trivial/default RuntimeBackend (runtime/ollama.py).
Provider is faked at the runtime.ollama.get_provider boundary, never the
real network, matching the pattern used across the rest of this test suite
(see tests/test_qa_precheck.py)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from symphysis.providers.base import ProviderResponse
from symphysis.runtime import ollama as ollama_runtime
from symphysis.runtime.base import TaskSpec


class _FakeProvider:
    def __init__(self, response_text: str):
        self.response_text = response_text
        self.calls = []

    def complete(self, messages, *, model, temperature, max_tokens, top_p=1.0, seed=None, **extra):
        self.calls.append({"messages": messages, "model": model, "temperature": temperature})
        return ProviderResponse(text=self.response_text, model=model, finish_reason="stop")


def _task(**overrides) -> TaskSpec:
    defaults = dict(
        agent_id="a1",
        did="did:key:z6Mktest",
        messages=[{"role": "user", "content": "hi"}],
        model_provider="ollama",
        model_name="qwen2.5:14b",
        temperature=0.7,
        max_tokens=1024,
    )
    defaults.update(overrides)
    return TaskSpec(**defaults)


def test_spawn_returns_handle_carrying_the_task(monkeypatch):
    backend = ollama_runtime.DirectCompletionBackend()
    task = _task()
    handle = backend.spawn(task)
    assert handle.agent_id == "a1"
    assert handle.backend_name == "direct_completion"
    assert handle.task is task


def test_stream_events_yields_exactly_one_raw_completion(monkeypatch):
    fake = _FakeProvider("the answer")
    monkeypatch.setattr(ollama_runtime, "get_provider", lambda name: fake)

    backend = ollama_runtime.DirectCompletionBackend()
    handle = backend.spawn(_task())
    events = list(backend.stream_events(handle))

    assert len(events) == 1
    assert events[0].kind == "raw_completion"
    assert events[0].payload["response"]["text"] == "the answer"
    assert events[0].payload["response"]["finish_reason"] == "stop"
    assert fake.calls[0]["model"] == "qwen2.5:14b"
    assert fake.calls[0]["temperature"] == 0.7


def test_stop_is_a_no_op(monkeypatch):
    fake = _FakeProvider("x")
    monkeypatch.setattr(ollama_runtime, "get_provider", lambda name: fake)
    backend = ollama_runtime.DirectCompletionBackend()
    handle = backend.spawn(_task())
    backend.stop(handle)  # must not raise
