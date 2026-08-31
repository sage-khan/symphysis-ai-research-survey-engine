"""Permission checks derived from an AgentCard's PermissionsSpec.

Enforced, not advisory: an agent whose card does not grant a scope is
refused before any file is read or any provider is called, rather than the
scope being documentation of an intended limit.

The actual grant/deny logic lives in `policy/engine.py` (the one
authorization decision point in this codebase); this module is the
domain-specific caller that knows what an AgentCard's PermissionsSpec looks
like and asks engine.py the right question.
"""

from __future__ import annotations

from ..agent_card import PermissionsSpec
from . import engine


class PermissionError_(Exception):
    """Distinct name from the builtin PermissionError to avoid confusing the
    two in a traceback: this is an AgentCard policy violation, not an OS one."""


def check_data_scope(path: str, permissions: PermissionsSpec) -> None:
    if not permissions.data_scopes:
        raise PermissionError_(
            f"Agent card grants no data_scopes, but a data path was requested: {path}. "
            "Add the path (or a glob covering it) to permissions.data_scopes."
        )
    normalized = engine.normalize_path(path)
    if not any(engine.covered(normalized, scope) for scope in permissions.data_scopes):
        raise PermissionError_(
            f"Path {path!r} is not covered by any of this agent's data_scopes {permissions.data_scopes!r}."
        )


def check_provider_allowed(provider_name: str, permissions: PermissionsSpec) -> None:
    if not engine.allowed(provider_name, permissions.allowed_providers):
        raise PermissionError_(
            f"Provider {provider_name!r} is not in this agent's allowed_providers {permissions.allowed_providers!r}."
        )
