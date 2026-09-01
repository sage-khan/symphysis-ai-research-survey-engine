import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from symphysis.instruments.bwm import BWMInstrument
from symphysis.instruments.bwm_two_stage import (
    assemble_bwm_payload,
    build_best_worst_prompt,
    build_ratings_prompt,
    parse_best_worst,
    parse_ratings,
)

CODES = ["DVS", "F", "E", "A"]
LABELS = {"DVS": "Data Value Score", "F": "Feasibility", "E": "Economic Value", "A": "Attack Resistance"}


def test_build_best_worst_prompt_names_every_code():
    prompt = build_best_worst_prompt(CODES, LABELS)
    for code in CODES:
        assert code in prompt


def test_parse_best_worst_happy_path():
    result = parse_best_worst("Best factor: DVS\nWorst factor: A\n", CODES)
    assert result.valid
    assert result.best == "DVS"
    assert result.worst == "A"


def test_parse_best_worst_tolerates_trailing_commentary():
    text = "Best factor: E (Economic Value)\nWorst factor: A (assuming other criteria hold)\n"
    result = parse_best_worst(text, CODES)
    assert result.valid
    assert result.best == "E"
    assert result.worst == "A"


def test_parse_best_worst_rejects_unknown_code():
    result = parse_best_worst("Best factor: ZZZ\nWorst factor: A\n", CODES)
    assert not result.valid
    assert any("ZZZ" in e for e in result.errors)


def test_parse_best_worst_rejects_same_best_and_worst():
    result = parse_best_worst("Best factor: DVS\nWorst factor: DVS\n", CODES)
    assert not result.valid


def test_parse_best_worst_rejects_missing_line():
    result = parse_best_worst("Best factor: DVS\n", CODES)
    assert not result.valid
    assert any("Worst factor" in e for e in result.errors)


def test_ratings_prompt_names_real_codes_not_placeholders():
    # This is the actual fix: no "<other criteria>" placeholder left for
    # the model to resolve on its own -- every line must name a real code.
    prompt = build_ratings_prompt("DVS", "A", ["F", "E"], LABELS)
    assert "DVS vs F" in prompt
    assert "DVS vs E" in prompt
    assert "DVS vs A" in prompt
    assert "F vs A" in prompt
    assert "E vs A" in prompt


def test_parse_ratings_happy_path():
    text = "DVS vs F: 7\nDVS vs E: 6\nDVS vs A: 9\nF vs A: 3\nE vs A: 2\n"
    result = parse_ratings(text, "DVS", "A", ["F", "E"])
    assert result.valid, result.errors
    assert result.ratings[("DVS", "F")] == 7
    assert result.ratings[("F", "A")] == 3


def test_parse_ratings_flags_missing_line_instead_of_guessing():
    # Only 4 of the 5 required lines present -- must fail, never fabricate.
    text = "DVS vs F: 7\nDVS vs E: 6\nDVS vs A: 9\nF vs A: 3\n"
    result = parse_ratings(text, "DVS", "A", ["F", "E"])
    assert not result.valid
    assert any("E vs A" in e for e in result.errors)
    assert ("E", "A") not in result.ratings


def test_parse_ratings_rejects_out_of_range_value():
    text = "DVS vs F: 15\nDVS vs E: 6\nDVS vs A: 9\nF vs A: 3\nE vs A: 2\n"
    result = parse_ratings(text, "DVS", "A", ["F", "E"])
    assert not result.valid


def test_assemble_bwm_payload_matches_production_schema():
    ratings = {
        ("DVS", "F"): 7, ("DVS", "E"): 6, ("DVS", "A"): 9,
        ("F", "A"): 3, ("E", "A"): 2,
    }
    payload = assemble_bwm_payload(CODES, "DVS", "A", ratings, "test reasoning")

    assert payload["best_to_others"]["DVS"] == 1  # self-comparison
    assert payload["others_to_worst"]["A"] == 1  # self-comparison
    # best-vs-worst must appear identically in both vectors
    assert payload["best_to_others"]["A"] == payload["others_to_worst"]["DVS"] == 9

    import json
    result = BWMInstrument().parse(json.dumps(payload), {"dimensions": CODES})
    assert result.valid, result.errors


def test_assemble_bwm_payload_raises_on_incomplete_ratings():
    # Deliberately missing (E, A) -- must raise, never silently omit/guess.
    ratings = {("DVS", "F"): 7, ("DVS", "E"): 6, ("DVS", "A"): 9, ("F", "A"): 3}
    try:
        assemble_bwm_payload(CODES, "DVS", "A", ratings, "test reasoning")
        assert False, "expected KeyError for missing rating"
    except KeyError:
        pass
