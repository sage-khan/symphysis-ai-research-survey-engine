"""Instrument interface: BWM is the first implementation; AHP and others plug
in the same way without touching the orchestrator, providers, or storage."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Protocol


@dataclass
class InstrumentResult:
    """A single agent's parsed, schema-valid answer to one instrument run."""

    valid: bool
    payload: Dict[str, Any]     # instrument-specific structured answer
    errors: List[str]           # populated when valid is False


class Instrument(Protocol):
    """An instrument owns three things: how to build the prompt for an agent,
    how to parse a raw model completion into structured data, and how to
    validate that structured data against the instrument's own schema."""

    name: str

    def build_messages(self, agent_role_description: str, context_chunks: List[str], params: Dict[str, Any]) -> List[Dict[str, str]]:
        ...

    def parse(self, raw_text: str, params: Dict[str, Any]) -> InstrumentResult:
        ...
