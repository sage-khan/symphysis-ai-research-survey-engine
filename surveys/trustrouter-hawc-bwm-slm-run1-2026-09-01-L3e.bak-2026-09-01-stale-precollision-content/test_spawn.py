import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from symphysis.agent_card import ModelSpec, new_card
from symphysis.audit.logger import SurveyStorage
from symphysis.identity.credentials import verify_credential
from symphysis.identity.did import AgentIdentity
from symphysis.policy.capability import KNOWLEDGE_REPO, RAG_RETRIEVAL, WEB_SEARCH
from symphysis.spawning import lineage, spawn


def _card(tmp_path: Path, agent_id: str = "spawn-test-agent", **kwargs):
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("Role: {role}\n{role_description}\n", encoding="utf-8")
    return new_card(
        agent_id=agent_id,
        role="Data Engineer",
        role_description="A test persona.",
        system_prompt_template=str(prompt),
        model=ModelSpec(provider="ollama", name="test-model"),
        did_seed="test-seed",
        **kwargs,
    )


def test_declare_root_writes_declaration_and_lineage_edge(tmp_path):
    card = _card(tmp_path, tools=["web_search"])
    storage = SurveyStorage(tmp_path / "survey")

    declaration = spawn.declare_root(storage, card, survey_id="test-survey")

    assert declaration["parent_did"] is None
    assert declaration["spawned_by"] == "orchestrator"
    assert declaration["did"] == card.did.id
    assert set(declaration["capabilities_requested"]) == {KNOWLEDGE_REPO, WEB_SEARCH}
    # A root spawn's granted capabilities equal what was requested: there is
    # no parent to attenuate against.
    assert declaration["capabilities_granted"] == declaration["capabilities_requested"]

    on_disk = json.loads((storage.agent_dir(card.agent_id) / "spawn_declaration.json").read_text())
    assert on_disk == declaration

    edges = lineage._read(storage)
    assert len(edges) == 1
    assert edges[0]["parent_did"] is None
    assert edges[0]["child_did"] == card.did.id


def test_declare_root_is_first_conversation_trace_entry(tmp_path):
    card = _card(tmp_path)
    storage = SurveyStorage(tmp_path / "survey")
    spawn.declare_root(storage, card, survey_id="test-survey")

    conv_path = storage.agent_dir(card.agent_id) / "conversation.jsonl"
    lines = conv_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    first = json.loads(lines[0])
    assert first["kind"] == "spawn_declared"
    assert first["did"] == card.did.id


def test_mint_child_produces_deterministic_did_and_valid_credential():
    parent = AgentIdentity.generate_deterministic("parent-agent", "seed-v1")
    result = spawn.mint_child(parent, "child-agent", spawn_id="spawn-001")

    assert result.identity.did.startswith("did:key:z")
    assert verify_credential(result.credential)
    assert result.credential["issuer"] == parent.did
    assert result.credential["credentialSubject"]["childDid"] == result.identity.did
    assert result.credential["credentialSubject"]["spawnId"] == "spawn-001"

    # Deterministic: minting the same child twice from the same parent
    # reproduces the identical DID.
    again = spawn.mint_child(parent, "child-agent", spawn_id="spawn-002")
    assert again.identity.did == result.identity.did


def test_mint_child_random_is_not_reproducible():
    parent = AgentIdentity.generate_deterministic("parent-agent", "seed-v1")
    a = spawn.mint_child(parent, "child-agent", deterministic=False)
    b = spawn.mint_child(parent, "child-agent", deterministic=False)
    assert a.identity.did != b.identity.did


def test_declare_child_attenuates_capabilities_to_parent_intersection(tmp_path):
    parent = AgentIdentity.generate_deterministic("parent-agent", "seed-v1")
    child_card = _card(tmp_path, agent_id="child-agent")
    storage = SurveyStorage(tmp_path / "survey")

    minted = spawn.mint_child(parent, "child-agent")
    declaration = spawn.declare_child(
        storage,
        child=minted,
        child_agent_id="child-agent",
        role="Data Engineer",
        parent=parent,
        parent_granted_capabilities=[KNOWLEDGE_REPO],  # parent does NOT hold web_search
        capabilities_requested=[KNOWLEDGE_REPO, WEB_SEARCH],
        model=child_card.model,
        survey_id="test-survey",
        runtime_backend="openmanus",
    )

    assert declaration["parent_did"] == parent.did
    assert declaration["spawned_by"] == f"agent:{parent.agent_id}"
    assert declaration["capabilities_requested"] == [KNOWLEDGE_REPO, WEB_SEARCH]
    # WEB_SEARCH was requested but the parent never held it: attenuated away.
    assert declaration["capabilities_granted"] == [KNOWLEDGE_REPO]
    assert verify_credential(declaration["spawn_credential"])

    edges = lineage._read(storage)
    assert edges[0]["parent_did"] == parent.did
    assert edges[0]["child_did"] == minted.identity.did


def test_declare_child_can_grant_full_request_when_parent_holds_everything(tmp_path):
    parent = AgentIdentity.generate_deterministic("parent-agent", "seed-v1")
    child_card = _card(tmp_path, agent_id="child-agent-2")
    storage = SurveyStorage(tmp_path / "survey")
    minted = spawn.mint_child(parent, "child-agent-2")

    declaration = spawn.declare_child(
        storage,
        child=minted,
        child_agent_id="child-agent-2",
        role="Data Engineer",
        parent=parent,
        parent_granted_capabilities=[KNOWLEDGE_REPO, RAG_RETRIEVAL, WEB_SEARCH],
        capabilities_requested=[RAG_RETRIEVAL, WEB_SEARCH],
        model=child_card.model,
        survey_id="test-survey",
        runtime_backend="openmanus",
    )
    assert declaration["capabilities_granted"] == [RAG_RETRIEVAL, WEB_SEARCH]
