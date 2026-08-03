import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentic_survey.instruments.hierarchical_bwm import HierarchicalBWMInstrument

PARAMS = {
    "composite_formula": "TrustRouter = DVS x F x (1 + E) x A",
    "levels": [
        {"id": "L1", "name": "Top-level factors", "description": "d1", "dimensions": ["DVS", "F", "E", "A"]},
        {
            "id": "L2", "name": "Six trust dimensions", "description": "d2",
            "dimensions": ["Q", "PT", "V", "IC", "L", "C"],
            "parent_level": "L1", "parent_criterion": "DVS",
        },
    ],
}


def _level_answer(codes, best, worst):
    return {
        "best": best,
        "worst": worst,
        "best_to_others": {c: (1 if c == best else 3) for c in codes},
        "others_to_worst": {c: (1 if c == worst else 3) for c in codes},
        "reasoning": f"{best} matters most, {worst} matters least.",
    }


def _valid_payload():
    return {
        "levels": {
            "L1": _level_answer(["DVS", "F", "E", "A"], "DVS", "F"),
            "L2": _level_answer(["Q", "PT", "V", "IC", "L", "C"], "C", "IC"),
        },
        "sources_used": ["general_knowledge"],
    }


def test_build_messages_includes_every_level_and_its_dimensions():
    instrument = HierarchicalBWMInstrument()
    messages = instrument.build_messages("You are a blockchain trust specialist.", [], PARAMS)
    user_content = messages[1]["content"]
    assert "Level L1" in user_content
    assert "Level L2" in user_content
    for code in ["DVS", "F", "E", "A", "Q", "PT", "V", "IC", "L", "C"]:
        assert code in user_content
    assert "TrustRouter = DVS x F x (1 + E) x A" in user_content


def test_parse_accepts_a_well_formed_multi_level_response():
    instrument = HierarchicalBWMInstrument()
    raw = f"Here is my answer:\n{json.dumps(_valid_payload())}\nThanks."
    result = instrument.parse(raw, PARAMS)
    assert result.valid, result.errors
    assert result.payload["levels"]["L1"]["best"] == "DVS"
    assert result.payload["levels"]["L2"]["best"] == "C"


def test_parse_rejects_a_missing_level():
    instrument = HierarchicalBWMInstrument()
    payload = _valid_payload()
    del payload["levels"]["L2"]
    result = instrument.parse(json.dumps(payload), PARAMS)
    assert not result.valid
    assert any("L2" in e for e in result.errors)


def test_parse_rejects_an_invalid_code_in_one_level():
    instrument = HierarchicalBWMInstrument()
    payload = _valid_payload()
    payload["levels"]["L1"]["best"] = "NOT_A_REAL_CODE"
    result = instrument.parse(json.dumps(payload), PARAMS)
    assert not result.valid


def test_parse_rejects_best_equals_worst_within_a_level():
    instrument = HierarchicalBWMInstrument()
    payload = _valid_payload()
    payload["levels"]["L2"]["worst"] = payload["levels"]["L2"]["best"]
    result = instrument.parse(json.dumps(payload), PARAMS)
    assert not result.valid


def test_parse_rejects_non_json_text():
    instrument = HierarchicalBWMInstrument()
    result = instrument.parse("I think DVS matters most.", PARAMS)
    assert not result.valid


def test_build_messages_lists_available_source_tags_when_context_present():
    instrument = HierarchicalBWMInstrument()
    messages = instrument.build_messages(
        "You are a blockchain trust specialist.",
        ["[role knowledge: blockchain_trust_specialist] some primer"],
        PARAMS,
    )
    assert '"role knowledge: blockchain_trust_specialist"' in messages[1]["content"]
