import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from symphysis.runtime.base import Event, RunHandle, TaskSpec


def test_task_spec_defaults():
    task = TaskSpec(
        agent_id="a1",
        did="did:key:z6Mktest",
        messages=[{"role": "user", "content": "hi"}],
        model_provider="ollama",
        model_name="qwen2.5:14b",
        temperature=0.7,
        max_tokens=1024,
    )
    assert task.top_p == 1.0
    assert task.seed is None
    assert task.capabilities_granted == []
    assert task.extra == {}


def test_run_handle_and_event_are_plain_dataclasses():
    handle = RunHandle(agent_id="a1", backend_name="direct_completion")
    assert handle.agent_id == "a1"
    event = Event(kind="raw_completion", payload={"x": 1})
    assert event.kind == "raw_completion"
    assert event.payload == {"x": 1}
