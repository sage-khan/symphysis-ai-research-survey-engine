"""Tests for instruments/setup_review.py: build_messages/parse only, no
Agent/provider involved (see test_pipeline.py for the full spawn+run path)."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from symphysis.instruments.setup_review import SetupReviewInstrument

PARAMS = {
    "deterministic_problems": ["survey.yaml: instrument_params.dimensions is empty for instrument 'bwm'"],
    "survey_yaml_text": "id: s1\ntitle: Survey 1\ninstrument: bwm\n",
    "agent_cards_text": ['{"agent_id": "panel-agent-1"}'],
}


def test_build_messages_includes_deterministic_problems_and_cards():
    messages = SetupReviewInstrument().build_messages("You are a reviewer.", [], PARAMS)
    assert messages[0] == {"role": "system", "content": "You are a reviewer."}
    user = messages[1]["content"]
    assert "instrument_params.dimensions is empty" in user
    assert "panel-agent-1" in user
    assert "id: s1" in user


def test_build_messages_appends_context_chunks():
    messages = SetupReviewInstrument().build_messages("role", ["[ref] some context"], PARAMS)
    assert "some context" in messages[1]["content"]


def test_parse_accepts_well_formed_findings():
    raw = json.dumps(
        {
            "findings": [
                {
                    "severity": "warning",
                    "area": "dimensions",
                    "finding": "X is ambiguous.",
                    "proposed_fix": "Clarify X.",
                }
            ],
            "summary": "Mostly ready.",
        }
    )
    result = SetupReviewInstrument().parse(raw, PARAMS)
    assert result.valid
    assert result.payload["findings"][0]["area"] == "dimensions"


def test_parse_accepts_empty_findings_list():
    raw = json.dumps({"findings": [], "summary": "Looks fine."})
    result = SetupReviewInstrument().parse(raw, PARAMS)
    assert result.valid


def test_parse_rejects_missing_findings_key():
    raw = json.dumps({"summary": "Looks fine."})
    result = SetupReviewInstrument().parse(raw, PARAMS)
    assert not result.valid
    assert any("findings" in e for e in result.errors)


def test_parse_rejects_unknown_severity():
    raw = json.dumps(
        {"findings": [{"severity": "catastrophic", "area": "x", "finding": "y", "proposed_fix": "z"}], "summary": "s"}
    )
    result = SetupReviewInstrument().parse(raw, PARAMS)
    assert not result.valid
    assert any("severity" in e for e in result.errors)


def test_parse_rejects_missing_json_object():
    result = SetupReviewInstrument().parse("not json at all", PARAMS)
    assert not result.valid
    assert result.payload == {}
