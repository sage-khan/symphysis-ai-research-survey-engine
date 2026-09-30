import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from symphysis.instruments.hierarchical_bwm import HierarchicalBWMInstrument

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


def test_build_messages_includes_the_ratio_vs_score_warning_once():
    # Regression test: an earlier version of this instrument's per-level
    # template omitted the "this is a ratio, not an absolute score, never 9
    # for self-comparison" warning that instruments/bwm.py's flat template
    # already carries (added there after real Ollama models rated
    # Best-to-itself as 9). qwen2.5:14b reproduced exactly that failure
    # ("best_to_others[best] must be 1, got 9") on a live hierarchical_bwm
    # run once the per-level template dropped the warning. State it once in
    # the shared intro rather than per level, to avoid repeating it seven
    # times in one prompt.
    instrument = HierarchicalBWMInstrument()
    messages = instrument.build_messages("You are a blockchain trust specialist.", [], PARAMS)
    user_content = messages[1]["content"]
    assert "never 9" in user_content
    assert user_content.count("RATIO") == 1


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


def test_parse_reports_a_self_rating_error_in_every_level_that_has_one():
    # Regression test: a model with one systematic misconvention (rating
    # Best-to-itself as 9, an "importance score" reading, instead of the
    # correct ratio-to-self of 1) applies it identically across every
    # level, not just the first. The parser previously gated each level's
    # self-rating check on whether the shared `errors` list was still
    # empty, so once L1's mistake was recorded, L2's identical mistake
    # was silently never checked at all, and a repair loop shown only
    # L1's error could never learn about L2's. Both must be reported from
    # a single parse call so one repair turn can fix everything at once.
    instrument = HierarchicalBWMInstrument()
    payload = _valid_payload()
    payload["levels"]["L1"]["best_to_others"]["DVS"] = 9  # best rated 9 against itself
    payload["levels"]["L2"]["best_to_others"]["C"] = 9  # same mistake, different level
    result = instrument.parse(json.dumps(payload), PARAMS)
    assert not result.valid
    assert any("L1" in e and "best_to_others[best] must be 1" in e for e in result.errors)
    assert any("L2" in e and "best_to_others[best] must be 1" in e for e in result.errors)


def test_build_messages_lists_available_source_tags_when_context_present():
    instrument = HierarchicalBWMInstrument()
    messages = instrument.build_messages(
        "You are a blockchain trust specialist.",
        ["[role knowledge: blockchain_trust_specialist] some primer"],
        PARAMS,
    )
    assert '"role knowledge: blockchain_trust_specialist"' in messages[1]["content"]


def test_levels_for_panel_returns_the_same_level_defs_as_params():
    instrument = HierarchicalBWMInstrument()
    assert instrument.levels_for_panel(PARAMS) == PARAMS["levels"]


def test_build_level_messages_scopes_to_one_level_only():
    instrument = HierarchicalBWMInstrument()
    messages = instrument.build_level_messages("L1", "You are a blockchain trust specialist.", [], PARAMS)
    user_content = messages[1]["content"]
    assert "Level L1" in user_content
    assert "Level L2" not in user_content
    for code in ["DVS", "F", "E", "A"]:
        assert code in user_content
    assert "- Q: Q" not in user_content  # L2's dimension_list line format never appears
    assert 'level_id="L1"' in user_content
    assert "instrument_submit" in user_content


def test_build_level_messages_includes_reference_material_when_present():
    instrument = HierarchicalBWMInstrument()
    messages = instrument.build_level_messages(
        "L1", "You are a blockchain trust specialist.", ["[general_knowledge] some primer"], PARAMS
    )
    assert "some primer" in messages[1]["content"]


def test_validate_level_accepts_a_correct_single_level_answer():
    instrument = HierarchicalBWMInstrument()
    answer = _level_answer(["DVS", "F", "E", "A"], "DVS", "F")
    result = instrument.validate_level("L1", answer, PARAMS)
    assert result.valid
    assert result.errors == []
    assert result.payload == {"L1": answer}


def test_validate_level_reports_the_same_error_message_as_parse_for_the_same_mistake():
    # Regression guard for the DRY refactor: parse() and validate_level()
    # must produce byte-identical error text for the same mistake, since
    # they now share _validate_level_fields() as their one implementation.
    instrument = HierarchicalBWMInstrument()
    bad_answer = _level_answer(["DVS", "F", "E", "A"], "DVS", "F")
    bad_answer["best_to_others"]["DVS"] = 9  # self-rating mistake

    whole_payload = _valid_payload()
    whole_payload["levels"]["L1"] = bad_answer
    whole_result = instrument.parse(json.dumps(whole_payload), PARAMS)

    level_result = instrument.validate_level("L1", bad_answer, PARAMS)

    assert not level_result.valid
    assert level_result.errors == [e for e in whole_result.errors if "L1" in e]


def test_validate_level_rejects_an_unknown_level_id():
    instrument = HierarchicalBWMInstrument()
    result = instrument.validate_level("L99", {}, PARAMS)
    assert not result.valid
    assert "Unknown level 'L99'" in result.errors[0]


def test_validate_level_isolates_one_level_from_a_totally_different_levels_mistakes():
    # The whole point of per-level validation: a mistake belonging to a
    # DIFFERENT level from the one being checked must never surface here.
    instrument = HierarchicalBWMInstrument()
    good_l1 = _level_answer(["DVS", "F", "E", "A"], "DVS", "F")
    result = instrument.validate_level("L1", good_l1, PARAMS)
    assert result.valid
    assert result.errors == []
