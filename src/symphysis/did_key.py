"""Real did:key identities + W3C-shaped Verifiable Credentials for agents.

Pattern follows project-cogtwins's veritas/svc-query/identity.py (Ed25519,
did:key, Ed25519Signature2020-style VC), which was verified there as a
correct, self-contained, dependency-light implementation. Two differences
from that pattern, both closing gaps that project's own design docs flag as
aspirational-but-unbuilt:

1. The seed an identity derives from is documented, explicitly, inside the
   agent's own card (see agent_card.py) rather than only a process-wide env
   var, so a single JSON file is what someone else needs to reproduce the
   identical DID (plus the shared secret seed value itself, communicated
   separately), not a JSON file plus an opaque out-of-band process.
2. `verify_credential` and `did_key_from_public` are exposed as free
   functions with no process-wide identity registry, since this app spawns
   many short-lived per-survey agents rather than a fixed cohort of long-
   running service agents.

Security note carried over unchanged from cogtwins: deterministic
derivation is a reproducibility property, not a security property. Anyone
who learns the seed can reconstruct the private key. Use `generate_random`
instead of `generate_deterministic` for any agent whose DID must resist
impersonation by someone who has seen its card.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

_B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
_ED25519_MULTICODEC = b"\xed\x01"


def _b58encode(data: bytes) -> str:
    n = int.from_bytes(data, "big")
    out = ""
    while n > 0:
        n, r = divmod(n, 58)
        out = _B58[r] + out
    pad = len(data) - len(data.lstrip(b"\x00"))
    return "1" * pad + out


def _b58decode(s: str) -> bytes:
    n = 0
    for ch in s:
        n = n * 58 + _B58.index(ch)
    body = n.to_bytes((n.bit_length() + 7) // 8, "big") if n else b""
    pad = len(s) - len(s.lstrip("1"))
    return b"\x00" * pad + body


def _canonical(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def did_key_from_public(pub: bytes) -> str:
    return "did:key:z" + _b58encode(_ED25519_MULTICODEC + pub)


def public_from_did_key(did: str) -> bytes:
    if not did.startswith("did:key:z"):
        raise ValueError("not a did:key")
    decoded = _b58decode(did[len("did:key:z"):])
    if not decoded.startswith(_ED25519_MULTICODEC):
        raise ValueError("not an Ed25519 did:key")
    return decoded[len(_ED25519_MULTICODEC):]


@dataclass
class AgentIdentity:
    agent_id: str
    did: str
    public_key_multibase: str
    deterministic: bool
    _sk: Ed25519PrivateKey

    @classmethod
    def generate_deterministic(cls, agent_id: str, seed: str) -> "AgentIdentity":
        """Reproducible identity: same agent_id + seed always yields the same
        DID. This is what makes an agent card, plus the shared seed, enough
        for someone else to respawn the identical agent identity."""
        seed32 = hashlib.sha256(f"{seed}:{agent_id}".encode()).digest()
        return cls._from_private_bytes(agent_id, seed32, deterministic=True)

    @classmethod
    def generate_random(cls, agent_id: str) -> "AgentIdentity":
        """Non-reproducible identity: use when impersonation resistance
        matters more than portability."""
        priv = Ed25519PrivateKey.generate().private_bytes_raw()
        return cls._from_private_bytes(agent_id, priv, deterministic=False)

    @classmethod
    def _from_private_bytes(cls, agent_id: str, priv: bytes, deterministic: bool) -> "AgentIdentity":
        sk = Ed25519PrivateKey.from_private_bytes(priv)
        pub = sk.public_key().public_bytes_raw()
        return cls(
            agent_id=agent_id,
            did=did_key_from_public(pub),
            public_key_multibase="z" + _b58encode(_ED25519_MULTICODEC + pub),
            deterministic=deterministic,
            _sk=sk,
        )

    def issue_credential(self, claim_type: str, subject: dict, spawn_id: str | None = None) -> dict:
        cs = {"agentId": self.agent_id, **subject}
        if spawn_id:
            cs["spawnId"] = spawn_id
        body = {
            "@context": ["https://www.w3.org/2018/credentials/v1"],
            "type": ["VerifiableCredential", claim_type],
            "issuer": self.did,
            "issuanceDate": datetime.now(timezone.utc).isoformat(),
            "credentialSubject": cs,
        }
        sig = self._sk.sign(_canonical(body))
        body["proof"] = {
            "type": "Ed25519Signature2020",
            "created": body["issuanceDate"],
            "verificationMethod": f"{self.did}#{self.did.split(':')[-1]}",
            "proofPurpose": "assertionMethod",
            "proofValue": "z" + _b58encode(sig),
        }
        return body


def verify_credential(vc: dict) -> bool:
    try:
        proof = vc.get("proof") or {}
        proof_value = proof.get("proofValue", "")
        if not proof_value.startswith("z"):
            return False
        sig = _b58decode(proof_value[1:])
        pub = public_from_did_key(vc.get("issuer", ""))
        body = {k: v for k, v in vc.items() if k != "proof"}
        Ed25519PublicKey.from_public_bytes(pub).verify(sig, _canonical(body))
        return True
    except Exception:
        return False
