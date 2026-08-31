import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from symphysis.agent_card import (
    AgentCardError,
    ModelSpec,
    PermissionsSpec,
    load_card,
    new_card,
    rehydrate_identity,
)


def _sample_card(agent_id="test-agent", did_seed="test-seed-v1"):
    return new_card(
        agent_id=agent_id,
        role="Test Role",
        role_description="A test agent.",
        system_prompt_template="config/prompts/expert_panel_system.txt",
        model=ModelSpec(provider="ollama", name="qwen2.5:14b"),
        permissions=PermissionsSpec(data_scopes=["surveys/x/rag_corpora/test/**"]),
        did_seed=did_seed,
    )


def test_new_card_has_valid_did_key():
    card = _sample_card()
    assert card.did.method == "did:key"
    assert card.did.id.startswith("did:key:z")
    assert card.did.deterministic is True


def test_same_agent_id_and_seed_give_same_did_across_cards():
    a = _sample_card(agent_id="agent-a")
    b = _sample_card(agent_id="agent-a")
    assert a.did.id == b.did.id


def test_write_and_load_card_roundtrip(tmp_path):
    card = _sample_card()
    path = tmp_path / "test-agent.json"
    card.write(path)

    loaded = load_card(path)
    assert loaded.agent_id == card.agent_id
    assert loaded.did.id == card.did.id
    assert loaded.model.provider == "ollama"
    assert loaded.permissions.data_scopes == ["surveys/x/rag_corpora/test/**"]


def test_load_card_rejects_missing_required_field(tmp_path):
    path = tmp_path / "broken.json"
    path.write_text(json.dumps({"schema_version": "1.0", "agent_id": "x"}), encoding="utf-8")
    with pytest.raises(AgentCardError):
        load_card(path)


def test_load_card_rejects_schema_version_mismatch(tmp_path):
    card = _sample_card()
    data = card.to_dict()
    data["schema_version"] = "99.0"
    path = tmp_path / "future.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(AgentCardError):
        load_card(path)


def test_rehydrate_identity_with_correct_seed(tmp_path):
    card = _sample_card(did_seed="known-seed")
    path = tmp_path / "test-agent.json"
    card.write(path)
    loaded = load_card(path)

    identity = rehydrate_identity(loaded, did_seed="known-seed")
    assert identity.did == card.did.id


def test_rehydrate_identity_with_wrong_seed_raises(tmp_path):
    card = _sample_card(did_seed="known-seed")
    path = tmp_path / "test-agent.json"
    card.write(path)
    loaded = load_card(path)

    with pytest.raises(AgentCardError):
        rehydrate_identity(loaded, did_seed="wrong-seed")


def test_rehydrate_identity_without_seed_raises(tmp_path):
    card = _sample_card()
    path = tmp_path / "test-agent.json"
    card.write(path)
    loaded = load_card(path)

    with pytest.raises(AgentCardError):
        rehydrate_identity(loaded, did_seed=None)


def test_runtime_backend_defaults_to_direct_completion():
    card = _sample_card()
    assert card.runtime_backend == "direct_completion"
    assert card.to_dict()["runtime_backend"] == "direct_completion"


def test_runtime_backend_round_trips_through_write_and_load(tmp_path):
    card = new_card(
        agent_id="openmanus-agent",
        role="Test Role",
        role_description="A test agent.",
        system_prompt_template="config/prompts/expert_panel_system.txt",
        model=ModelSpec(provider="ollama", name="qwen2.5:14b"),
        did_seed="test-seed-v1",
        runtime_backend="openmanus",
    )
    path = tmp_path / "openmanus-agent.json"
    card.write(path)
    loaded = load_card(path)
    assert loaded.runtime_backend == "openmanus"


def test_load_card_without_runtime_backend_field_defaults_to_direct_completion(tmp_path):
    # A card authored before this field existed: load_card must not choke on
    # its absence, and must default it to the behavior every such card
    # already has (a single direct provider call).
    card = _sample_card()
    data = card.to_dict()
    del data["runtime_backend"]
    path = tmp_path / "pre-existing-agent.json"
    path.write_text(json.dumps(data), encoding="utf-8")

    loaded = load_card(path)
    assert loaded.runtime_backend == "direct_completion"
