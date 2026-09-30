"""Tests for instruments/response_review.py: build_messages/parse only, no
Agent/provider involved (see test_pipeline.py for the full spawn+run path)."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from symphysis.instruments.response_review import ResponseReviewInstrument

PARAMS = {
    "survey_title": "Test Survey",
    "instrument": "bwm",
    "dimensions": ["A", "B"],
    "agent_responses": [
        {"agent_id": "panel-agent-1", "role": "Data Engineer", "answer": {"best": "A", "worst": "B"}, "reasoning": "A clearly outranks B."}
    ],
}


def test_build_messages_includes_agent_responses():
    messages = ResponseReviewInstrument().build_messages("You are a reviewer.", [], PARAMS)
    user = messages[1]["content"]
    assert "panel-agent-1" in user
    assert "A clearly outranks B." in user
    assert "Test Survey" in user


def test_parse_accepts_well_formed_findings():
    raw = json.dumps(
        {
            "findings": [{"agent_id": "panel-agent-1", "severity": "info", "finding": "Reasoning is thin."}],
            "summary": "Panel looks sound.",
        }
    )
    result = ResponseReviewInstrument().parse(raw, PARAMS)
    assert result.valid
    assert result.payload["findings"][0]["agent_id"] == "panel-agent-1"


def test_parse_rejects_finding_for_unknown_agent_id():
    raw = json.dumps(
        {"findings": [{"agent_id": "not-a-real-agent", "severity": "info", "finding": "x"}], "summary": "s"}
    )
    result = ResponseReviewInstrument().parse(raw, PARAMS)
    assert not result.valid
    assert any("not one of the reviewed" in e for e in result.errors)


def test_parse_accepts_empty_findings_list():
    raw = json.dumps({"findings": [], "summary": "All sound."})
    result = ResponseReviewInstrument().parse(raw, PARAMS)
    assert result.valid


def test_parse_rejects_unknown_severity():
    raw = json.dumps(
        {"findings": [{"agent_id": "panel-agent-1", "severity": "catastrophic", "finding": "x"}], "summary": "s"}
    )
    result = ResponseReviewInstrument().parse(raw, PARAMS)
    assert not result.valid
    assert any("severity" in e for e in result.errors)
