import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentic_survey.agent_card import ModelSpec, RagSpec, SamplingSpec, PermissionsSpec, GuardrailsSpec, new_card
from agentic_survey.guardrails import GuardedRun
from agentic_survey.instruments.base import InstrumentResult
from agentic_survey.providers.base import ProviderResponse
from agentic_survey.storage import SurveyStorage

INSTRUMENT_PARAMS = {
    "dimensions": ["Q", "PT", "C"],
    "dimension_labels": {"Q": "Quality", "PT": "Provenance Trust", "C": "Criticality"},
}


def _card(agent_id="test-agent"):
    return new_card(
        agent_id=agent_id,
        role="Test Role",
        role_description="A test agent.",
        system_prompt_template="config/prompts/expert_panel_system.txt",
        model=ModelSpec(provider="ollama", name="qwen2.5:14b"),
        rag=RagSpec(enabled=False),
        sampling=SamplingSpec(repeats=2),
        permissions=PermissionsSpec(allowed_providers=["ollama"]),
        guardrails=GuardrailsSpec(),
        did_seed="test-seed",
    )


def test_write_prompt_creates_readable_markdown(tmp_path):
    card_path = tmp_path / "test-agent.json"
    _card().write(card_path)
    storage = SurveyStorage(tmp_path)

    messages = [{"role": "system", "content": "You are a test agent."}, {"role": "user", "content": "Do the task."}]
    storage.write_prompt("test-agent", messages)

    prompt_path = storage.agent_dir("test-agent") / "prompt.md"
    assert prompt_path.exists()
    text = prompt_path.read_text()
    assert "You are a test agent." in text
    assert "Do the task." in text


def test_write_tool_call_logs_to_conversation(tmp_path):
    storage = SurveyStorage(tmp_path)
    storage.write_tool_call("test-agent", tool="rag_retrieval", detail={"corpus_path": "x/y", "retrieved_sources": ["a.md"]})

    conv_path = storage.agent_dir("test-agent") / "conversation.jsonl"
    lines = [json.loads(l) for l in conv_path.read_text().splitlines()]
    assert len(lines) == 1
    assert lines[0]["kind"] == "tool_call"
    assert lines[0]["tool"] == "rag_retrieval"
    assert lines[0]["retrieved_sources"] == ["a.md"]
    assert "logged_at" in lines[0]


def test_write_guarded_run_renders_filled_survey(tmp_path):
    card = _card()
    card_path = tmp_path / "test-agent.json"
    card.write(card_path)
    storage = SurveyStorage(tmp_path)
    storage.init_agent(card, card_path)

    accepted = [
        InstrumentResult(
            valid=True,
            payload={
                "best": "PT",
                "worst": "C",
                "best_to_others": {"Q": 2, "PT": 1, "C": 8},
                "others_to_worst": {"Q": 4, "PT": 8, "C": 1},
                "reasoning": "Provenance matters most here.",
            },
            errors=[],
        )
    ]
    run = GuardedRun(accepted=accepted, rejected=[], raw_completions=[ProviderResponse(text="{}")])

    storage.write_guarded_run("test-agent", run, card=card, instrument_params=INSTRUMENT_PARAMS)

    filled = (storage.agent_dir("test-agent") / "filled_survey.md").read_text()
    assert "test-agent" in filled
    assert "Test Role" in filled
    assert card.did.id in filled
    assert "| 0 | PT | C |" in filled
    assert "Provenance matters most here." in filled
    assert "Q (Quality)" in filled


def test_write_guarded_run_handles_zero_accepted_samples(tmp_path):
    card = _card()
    card_path = tmp_path / "test-agent.json"
    card.write(card_path)
    storage = SurveyStorage(tmp_path)
    storage.init_agent(card, card_path)

    run = GuardedRun(accepted=[], rejected=[{"raw_text": "garbage", "errors": ["bad"], "attempt": 0}], raw_completions=[])
    storage.write_guarded_run("test-agent", run, card=card, instrument_params=INSTRUMENT_PARAMS)

    filled = (storage.agent_dir("test-agent") / "filled_survey.md").read_text()
    assert "No sample passed the guardrails" in filled
