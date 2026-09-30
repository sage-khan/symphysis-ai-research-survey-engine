import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from symphysis.instruments.bwm import BWMInstrument

PARAMS = {"dimensions": ["Q", "PT", "V", "IC", "L", "C"], "dimension_labels": {}}


def _valid_payload():
    return {
        "best": "PT",
        "worst": "C",
        "best_to_others": {"Q": 2, "PT": 1, "V": 3, "IC": 4, "L": 2, "C": 8},
        "others_to_worst": {"Q": 4, "PT": 8, "V": 5, "IC": 3, "L": 4, "C": 1},
        "reasoning": "Provenance matters most for audit trails.",
    }


def test_parse_accepts_well_formed_response():
    instrument = BWMInstrument()
    raw = f"Here is my answer:\n{json.dumps(_valid_payload())}\nThanks."
    result = instrument.parse(raw, PARAMS)
    assert result.valid, result.errors


def test_parse_rejects_missing_dimension():
    instrument = BWMInstrument()
    payload = _valid_payload()
    del payload["best_to_others"]["C"]
    result = instrument.parse(json.dumps(payload), PARAMS)
    assert not result.valid
    assert any("missing ratings" in e for e in result.errors)


def test_parse_rejects_out_of_range_rating():
    instrument = BWMInstrument()
    payload = _valid_payload()
    payload["best_to_others"]["V"] = 15
    result = instrument.parse(json.dumps(payload), PARAMS)
    assert not result.valid


def test_parse_rejects_best_to_others_best_not_one():
    instrument = BWMInstrument()
    payload = _valid_payload()
    payload["best_to_others"]["PT"] = 3  # best rated against itself must be 1
    result = instrument.parse(json.dumps(payload), PARAMS)
    assert not result.valid
    assert any("best_to_others[best]" in e for e in result.errors)


def test_parse_rejects_non_json_text():
    instrument = BWMInstrument()
    result = instrument.parse("I think Provenance is most important.", PARAMS)
    assert not result.valid


def test_build_messages_includes_all_dimensions_and_context():
    instrument = BWMInstrument()
    messages = instrument.build_messages("You are a BIM coordinator.", ["[doc1] some grounding text"], PARAMS)
    assert messages[0]["role"] == "system"
    user_content = messages[1]["content"]
    for code in PARAMS["dimensions"]:
        assert code in user_content
    assert "grounding text" in user_content


def test_build_messages_lists_real_source_tags_when_context_is_present():
    instrument = BWMInstrument()
    messages = instrument.build_messages(
        "You are a data engineer.",
        ["[shared knowledge: kb.md] some text", "[role knowledge: data_engineer] some primer"],
        PARAMS,
    )
    user_content = messages[1]["content"]
    assert '"shared knowledge: kb.md"' in user_content
    assert '"role knowledge: data_engineer"' in user_content
    assert "sources_used" in user_content


def test_build_messages_falls_back_to_general_knowledge_only_with_no_context():
    instrument = BWMInstrument()
    messages = instrument.build_messages("You are a data engineer.", [], PARAMS)
    user_content = messages[1]["content"]
    assert '["general_knowledge"]' in user_content


def test_parse_accepts_a_response_with_sources_used():
    instrument = BWMInstrument()
    payload = _valid_payload()
    payload["sources_used"] = ["general_knowledge"]
    result = instrument.parse(json.dumps(payload), PARAMS)
    assert result.valid, result.errors
    assert result.payload["sources_used"] == ["general_knowledge"]


def test_parse_accepts_a_response_missing_sources_used_entirely():
    instrument = BWMInstrument()
    result = instrument.parse(json.dumps(_valid_payload()), PARAMS)
    assert result.valid, result.errors


def test_parse_rejects_sources_used_of_the_wrong_type():
    instrument = BWMInstrument()
    payload = _valid_payload()
    payload["sources_used"] = "general_knowledge"  # should be a list, not a bare string
    result = instrument.parse(json.dumps(payload), PARAMS)
    assert not result.valid
    assert any("sources_used" in e for e in result.errors)
