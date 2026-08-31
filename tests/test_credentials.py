import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from symphysis.identity.credentials import verify_credential
from symphysis.identity.did import AgentIdentity


def test_issue_and_verify_credential_roundtrip():
    identity = AgentIdentity.generate_deterministic("bim-coordinator", "seed-v1")
    vc = identity.issue_credential("BwmResponse", {"best": "PT", "worst": "C"}, spawn_id="spawn-001")
    assert verify_credential(vc)
    assert vc["credentialSubject"]["spawnId"] == "spawn-001"


def test_verify_credential_rejects_tampered_subject():
    identity = AgentIdentity.generate_deterministic("bim-coordinator", "seed-v1")
    vc = identity.issue_credential("BwmResponse", {"best": "PT", "worst": "C"})
    vc["credentialSubject"]["best"] = "Q"  # tamper after signing
    assert not verify_credential(vc)


def test_verify_credential_rejects_wrong_issuer_key():
    identity_a = AgentIdentity.generate_deterministic("agent-a", "seed")
    identity_b = AgentIdentity.generate_deterministic("agent-b", "seed")
    vc = identity_a.issue_credential("BwmResponse", {"best": "PT"})
    vc["issuer"] = identity_b.did  # claim it came from a different agent
    assert not verify_credential(vc)
