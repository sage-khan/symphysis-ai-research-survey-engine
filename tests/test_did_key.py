import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentic_survey.did_key import AgentIdentity, verify_credential, did_key_from_public, public_from_did_key


def test_deterministic_identity_is_reproducible():
    a = AgentIdentity.generate_deterministic("bim-coordinator", "seed-v1")
    b = AgentIdentity.generate_deterministic("bim-coordinator", "seed-v1")
    assert a.did == b.did
    assert a.public_key_multibase == b.public_key_multibase


def test_different_seed_or_agent_id_gives_different_did():
    a = AgentIdentity.generate_deterministic("bim-coordinator", "seed-v1")
    b = AgentIdentity.generate_deterministic("bim-coordinator", "seed-v2")
    c = AgentIdentity.generate_deterministic("structural-engineer", "seed-v1")
    assert a.did != b.did
    assert a.did != c.did


def test_did_key_format():
    identity = AgentIdentity.generate_deterministic("agent-x", "seed")
    assert identity.did.startswith("did:key:z")
    # round-trips through public_from_did_key
    pub = public_from_did_key(identity.did)
    assert did_key_from_public(pub) == identity.did


def test_random_identity_is_not_reproducible():
    a = AgentIdentity.generate_random("agent-x")
    b = AgentIdentity.generate_random("agent-x")
    assert a.did != b.did
    assert a.deterministic is False


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
