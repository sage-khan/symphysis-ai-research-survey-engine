"""Lightweight agent DID (decentralised identifier) scheme.

Not a full W3C DID method with a resolvable document/registry; a stable,
content-free identifier of the form did:veritas:agent:<uuid4> that ties an
agent instance to its persisted folder for the lifetime of a survey. If a
resolvable W3C DID/VC is later needed (e.g. to align with the DID/VC work in
CogTwins), this module is the seam to swap the generator without touching
callers.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class AgentDID:
    did: str
    agent_id: str
    created_at: str

    @classmethod
    def generate(cls, agent_id: str) -> "AgentDID":
        return cls(
            did=f"did:veritas:agent:{uuid.uuid4()}",
            agent_id=agent_id,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

    def write(self, path: Path) -> None:
        path.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "AgentDID":
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(**data)

    @classmethod
    def load_or_create(cls, path: Path, agent_id: str) -> "AgentDID":
        if path.exists():
            return cls.load(path)
        did = cls.generate(agent_id)
        did.write(path)
        return did
