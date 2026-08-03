import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentic_survey.instruments.ahp import AHPInstrument, build_full_matrix

PARAMS = {"dimensions": ["Q", "PT", "V"], "dimension_labels": {}}


def _valid_payload():
    return {
        "comparisons": {"Q_vs_PT": 3, "Q_vs_V": 5, "PT_vs_V": 2},
        "reasoning": "Quality matters most, provenance trust second.",
        "sources_used": ["general_knowledge"],
    }


def test_build_messages_lists_every_pair_exactly_once():
    instrument = AHPInstrument()
    messages = instrument.build_messages("You are a data engineer.", [], PARAMS)
    user_content = messages[1]["content"]
    assert "Q_vs_PT" in user_content
    assert "Q_vs_V" in user_content
    assert "PT_vs_V" in user_content
    # reversed pairs should not also appear
    assert "PT_vs_Q" not in user_content


def test_parse_accepts_well_formed_response():
    instrument = AHPInstrument()
    raw = f"Here is my answer:\n{json.dumps(_valid_payload())}\nThanks."
    result = instrument.parse(raw, PARAMS)
    assert result.valid, result.errors


def test_parse_rejects_missing_pair():
    instrument = AHPInstrument()
    payload = _valid_payload()
    del payload["comparisons"]["PT_vs_V"]
    result = instrument.parse(json.dumps(payload), PARAMS)
    assert not result.valid
    assert any("missing pairs" in e for e in result.errors)


def test_parse_rejects_non_positive_comparison():
    instrument = AHPInstrument()
    payload = _valid_payload()
    payload["comparisons"]["Q_vs_PT"] = -1
    result = instrument.parse(json.dumps(payload), PARAMS)
    assert not result.valid


def test_parse_rejects_an_unknown_pair():
    instrument = AHPInstrument()
    payload = _valid_payload()
    payload["comparisons"]["Q_vs_ZZZ"] = 3
    result = instrument.parse(json.dumps(payload), PARAMS)
    assert not result.valid
    assert any("unknown pair" in e for e in result.errors)


def test_parse_rejects_non_json_text():
    instrument = AHPInstrument()
    result = instrument.parse("Quality is most important.", PARAMS)
    assert not result.valid


def test_build_full_matrix_is_reciprocal_and_has_unit_diagonal():
    codes = ["Q", "PT", "V"]
    comparisons = {"Q_vs_PT": 3, "Q_vs_V": 5, "PT_vs_V": 2}
    matrix = build_full_matrix(codes, comparisons)
    assert matrix[0][0] == matrix[1][1] == matrix[2][2] == 1.0
    assert matrix[0][1] == 3.0
    assert matrix[1][0] == 1.0 / 3.0
    assert matrix[0][2] == 5.0
    assert matrix[2][0] == 1.0 / 5.0
