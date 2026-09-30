"""The RuntimeBackend protocol every execution backend implements.

Per docs/architecture/governance-layer-and-runtime-backends-plan.md §3-4
(Phase 2, task 11): this is the seam between the governance layer
(identity/policy/audit, and now spawning/) and whatever actually drives an
agent's turn-by-turn execution. `runtime/ollama.py` is the trivial default
(a single completion call, today's actual behavior, wrapped rather than
replaced); `runtime/openmanus.py` is the flagship multi-turn/tool-using
backend; `runtime/opencode.py` (Phase 5, not yet built) follows the same
protocol as an external-process adapter.

A backend never makes its own authorization decisions — every tool call it
drives must go through `tools/authorization.py`, which is the only place
`policy/engine.py` is consulted (per the plan doc's "one authorization
decision point" design principle).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, List, Protocol


@dataclass
class TaskSpec:
    """What a backend is asked to do for one agent turn: the same inputs
    Agent.run() already assembles today (system prompt, message history,
    hyperparameters), named so a backend doesn't need to know about
    AgentCard/AgentIdentity directly."""

    agent_id: str
    did: str
    messages: List[Dict[str, str]]
    model_provider: str
    model_name: str
    temperature: float
    max_tokens: int
    top_p: float = 1.0
    seed: int | None = None
    capabilities_granted: List[str] = field(default_factory=list)
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RunHandle:
    """Opaque handle a backend returns from spawn(); passed back into
    stream_events()/stop(). Backends may subclass this to carry their own
    internal state (e.g. an OpenManus agent instance)."""

    agent_id: str
    backend_name: str


@dataclass
class Event:
    """One event in a run's execution trace, shaped to be written straight
    into audit/logger.py's conversation.jsonl via the existing append_*
    methods rather than requiring a new sink. `kind` matches the vocabulary
    already used by TraceViewer.jsx's KIND_LABEL map plus any new kinds a
    backend introduces (e.g. "thought" for an OpenManus ReAct think() step)."""

    kind: str
    payload: Dict[str, Any] = field(default_factory=dict)


class RuntimeBackend(Protocol):
    """Every backend implements exactly these three operations. Backends are
    synchronous/generator-based, not async, matching the rest of this
    codebase (providers/*.py are all synchronous requests.post calls)."""

    name: str

    def spawn(self, task: TaskSpec) -> RunHandle:
        """Start (or prepare) a run for the given task. Must not block for
        the full duration of the run; `stream_events` does that."""
        ...

    def stream_events(self, handle: RunHandle) -> Iterator[Event]:
        """Yield this run's events in order as they occur, ending with a
        terminal event (kind="raw_completion" or "error"). For a
        single-completion backend (runtime/ollama.py) this yields exactly
        one event and returns; a multi-turn backend (runtime/openmanus.py)
        yields one event per ReAct step."""
        ...

    def stop(self, handle: RunHandle) -> None:
        """Best-effort cancellation. A backend with nothing to cancel (a
        single already-blocking completion call) may make this a no-op."""
        ...
