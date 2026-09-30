"""The trivial/default RuntimeBackend: a single completion call.

Per the plan doc's Phase 2 task 12: this wraps the existing
`providers/ollama_provider.py` unchanged rather than reimplementing the HTTP
call, so this stays the zero-marginal-cost, local-first default every survey
run keeps using unless an agent's card explicitly opts into a richer
backend (OpenManus). Despite the module name, this backend works with any
provider registered in `providers/__init__.py::get_provider`, not only
Ollama — "ollama" names the default/local-first case, matching the plan
doc's own module-tree naming.
"""

from __future__ import annotations

from typing import Iterator

from ..providers import get_provider
from .base import Event, RunHandle, TaskSpec


class DirectCompletionHandle(RunHandle):
    def __init__(self, agent_id: str, task: TaskSpec) -> None:
        super().__init__(agent_id=agent_id, backend_name="direct_completion")
        self.task = task


class DirectCompletionBackend:
    """Satisfies the RuntimeBackend protocol with exactly the single-call
    behavior Agent.run() already performs today via get_provider(...).complete(...).
    """

    name = "direct_completion"

    def spawn(self, task: TaskSpec) -> RunHandle:
        return DirectCompletionHandle(agent_id=task.agent_id, task=task)

    def stream_events(self, handle: RunHandle) -> Iterator[Event]:
        assert isinstance(handle, DirectCompletionHandle)
        task = handle.task
        provider = get_provider(task.model_provider)
        response = provider.complete(
            task.messages,
            model=task.model_name,
            temperature=task.temperature,
            max_tokens=task.max_tokens,
            top_p=task.top_p,
            seed=task.seed,
        )
        yield Event(
            kind="raw_completion",
            payload={
                "response": {
                    "text": response.text,
                    "raw": response.raw,
                    "model": response.model,
                    "finish_reason": response.finish_reason,
                }
            },
        )

    def stop(self, handle: RunHandle) -> None:
        # A single blocking completion call has nothing to cancel mid-flight.
        pass
