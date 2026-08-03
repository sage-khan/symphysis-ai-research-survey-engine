import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "web"))

from backend.analytics import compute_analytics


def _card(agent_id: str, role: str = "Role", provider: str = "ollama", model: str = "qwen2.5:14b", rag: bool = False) -> dict:
    return {
        "agent_id": agent_id,
        "role": role,
        "model": {"provider": provider, "name": model},
        "rag": {"enabled": rag},
        "did": {"id": f"did:key:{agent_id}"},
    }


def _write(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, (dict, list)):
        path.write_text(json.dumps(data), encoding="utf-8")
    else:
        path.write_text(data, encoding="utf-8")


def test_classifies_each_agent_status_correctly(tmp_path: Path):
    survey_dir = tmp_path / "some-survey"
    agents_dir = survey_dir / "agents"

    # contributed: two accepted samples
    _write(agents_dir / "a-contributed.json", _card("a-contributed"))
    _write(
        agents_dir / "a-contributed" / "result.json",
        {
            "agent_id": "a-contributed",
            "accepted_count": 2,
            "rejected_count": 1,
            "accepted_payloads": [
                {"best": "Q", "worst": "C", "reasoning": "r0"},
                {"best": "IC", "worst": "C", "reasoning": "r1"},
            ],
        },
    )

    # zero_accepted: ran fully, guardrails rejected everything
    _write(agents_dir / "b-zero.json", _card("b-zero"))
    _write(
        agents_dir / "b-zero" / "result.json",
        {"agent_id": "b-zero", "accepted_count": 0, "rejected_count": 15, "accepted_payloads": []},
    )

    # pending_manual: result.json present but empty, manual_input has a pending prompt
    _write(agents_dir / "c-pending.json", _card("c-pending", provider="manual", model="gemini-2.5-pro"))
    _write(
        agents_dir / "c-pending" / "result.json",
        {"agent_id": "c-pending", "accepted_count": 0, "rejected_count": 0, "accepted_payloads": []},
    )
    _write(agents_dir / "c-pending" / "manual_input" / "prompt_00.md", "prompt text")

    # skipped: card exists, runtime folder exists, but no result.json at all
    _write(agents_dir / "d-skipped.json", _card("d-skipped", provider="anthropic", model="claude-opus-5"))
    (agents_dir / "d-skipped").mkdir(parents=True, exist_ok=True)
    _write(agents_dir / "d-skipped" / "card.json", _card("d-skipped"))

    # not_run: card exists, no runtime folder at all
    _write(agents_dir / "e-not-run.json", _card("e-not-run"))

    result = compute_analytics(survey_dir)

    statuses = {a["agent_id"]: a["status"] for a in result["per_agent"]}
    assert statuses == {
        "a-contributed": "contributed",
        "b-zero": "zero_accepted",
        "c-pending": "pending_manual",
        "d-skipped": "skipped",
        "e-not-run": "not_run",
    }
    assert result["summary"] == {
        "contributed": 1,
        "zero_accepted": 1,
        "pending_manual": 1,
        "skipped": 1,
        "in_progress": 0,
        "not_run": 1,
    }

    contributed = next(a for a in result["per_agent"] if a["agent_id"] == "a-contributed")
    assert len(contributed["samples"]) == 2
    assert contributed["samples"][0]["best"] == "Q"
    assert contributed["samples"][0]["reasoning"] == "r0"

    freq = {row["criterion"]: row for row in result["best_worst_frequency"]}
    assert freq["Q"] == {"criterion": "Q", "best_count": 1, "worst_count": 0}
    assert freq["C"] == {"criterion": "C", "best_count": 0, "worst_count": 2}
    assert freq["IC"] == {"criterion": "IC", "best_count": 1, "worst_count": 0}


def test_empty_survey_has_no_agents(tmp_path: Path):
    survey_dir = tmp_path / "empty-survey"
    (survey_dir / "agents").mkdir(parents=True)
    result = compute_analytics(survey_dir)
    assert result["per_agent"] == []
    assert result["best_worst_frequency"] == []
    assert result["summary"] == {
        "contributed": 0, "zero_accepted": 0, "pending_manual": 0,
        "skipped": 0, "in_progress": 0, "not_run": 0,
    }


def test_no_result_json_is_in_progress_while_running_but_skipped_once_stopped(tmp_path: Path):
    survey_dir = tmp_path / "live-survey"
    agents_dir = survey_dir / "agents"

    _write(agents_dir / "f-mid-flight.json", _card("f-mid-flight"))
    (agents_dir / "f-mid-flight").mkdir(parents=True, exist_ok=True)
    _write(agents_dir / "f-mid-flight" / "card.json", _card("f-mid-flight"))

    # While the survey is still running, an agent with no result.json yet
    # has not necessarily failed, it just hasn't finished: must not be
    # reported as "skipped" (which implies the orchestrator already gave
    # up on it).
    running_result = compute_analytics(survey_dir, is_running=True)
    assert running_result["per_agent"][0]["status"] == "in_progress"
    assert running_result["summary"]["in_progress"] == 1
    assert running_result["summary"]["skipped"] == 0

    # Once the survey is no longer running, the same on-disk state (still
    # no result.json) means the orchestrator really did move on without
    # ever producing one for this agent: now it is genuinely "skipped".
    stopped_result = compute_analytics(survey_dir, is_running=False)
    assert stopped_result["per_agent"][0]["status"] == "skipped"
    assert stopped_result["summary"]["skipped"] == 1
    assert stopped_result["summary"]["in_progress"] == 0
