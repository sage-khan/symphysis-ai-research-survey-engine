"""W3C-shaped Verifiable Credential issuance and verification.

Separated from `identity/did.py` deliberately: `did.py` is "what an
identity is" (a keypair and its did:key encoding); this module is "what an
identity can attest to" (a signed claim about something that agent did or
produced). Keeping the split lets a future consumer depend on DID
resolution/verification alone without pulling in credential-shape logic it
may not need.

`AgentIdentity.issue_credential` (see `did.py`) is a thin delegating method
to `issue_credential` below, so existing call sites
(`identity.issue_credential(...)`) are unaffected by this module split.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from .did import _b58decode, _b58encode, public_from_did_key

if TYPE_CHECKING:
    from .did import AgentIdentity


def _canonical(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def issue_credential(
    identity: "AgentIdentity", claim_type: str, subject: dict, spawn_id: str | None = None
) -> dict:
    cs = {"agentId": identity.agent_id, **subject}
    if spawn_id:
        cs["spawnId"] = spawn_id
    body = {
        "@context": ["https://www.w3.org/2018/credentials/v1"],
        "type": ["VerifiableCredential", claim_type],
        "issuer": identity.did,
        "issuanceDate": datetime.now(timezone.utc).isoformat(),
        "credentialSubject": cs,
    }
    sig = identity.sign(_canonical(body))
    body["proof"] = {
        "type": "Ed25519Signature2020",
        "created": body["issuanceDate"],
        "verificationMethod": f"{identity.did}#{identity.did.split(':')[-1]}",
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
