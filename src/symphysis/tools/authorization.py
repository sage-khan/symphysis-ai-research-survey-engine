"""Capability check for a single tool call.

Distinct from `policy/authorization.py` (which checks an AgentCard's
`PermissionsSpec` data-scope/provider allowlists): this checks the calling
agent's `capabilities_granted`, the set computed once at spawn time (see
`spawning/spawn.py`) and written to `spawn_declaration.json` before the
agent did anything else. Reading it back from disk here, rather than
threading a live capability list through every call site, keeps the spawn
declaration itself the single source of truth an auditor can check against
independently of how a given tool call happened to be wired.

Per docs/architecture/governance-layer-and-runtime-backends-plan.md's "one
authorization decision point" design principle: the actual membership test
is `policy/engine.py::allowed`, not reimplemented here.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Optional

from ..policy import engine

if TYPE_CHECKING:
    from ..audit.logger import SurveyStorage


class ToolAuthorizationError(Exception):
    """A tool call was attempted without the capability it requires."""


def check_capability(storage: "SurveyStorage", agent_id: str, capability: Optional[str]) -> None:
    """Raises ToolAuthorizationError unless `capability` is in the calling
    agent's own spawn_declaration.json capabilities_granted. `capability=None`
    (a tool with no capability gate, e.g. citation_verify — it reads no
    protected resource, only checks a list the agent already produced)
    always passes."""
    if capability is None:
        return
    decl_path = storage.agent_dir(agent_id) / "spawn_declaration.json"
    if not decl_path.exists():
        raise ToolAuthorizationError(
            f"Agent {agent_id!r} has no spawn_declaration.json; cannot authorize a "
            f"{capability!r} tool call for an agent that was never declared."
        )
    declaration = json.loads(decl_path.read_text(encoding="utf-8"))
    granted = declaration.get("capabilities_granted", [])
    if not engine.allowed(capability, granted):
        raise ToolAuthorizationError(
            f"Agent {agent_id!r} was not granted capability {capability!r} "
            f"(capabilities_granted: {granted!r})."
        )
