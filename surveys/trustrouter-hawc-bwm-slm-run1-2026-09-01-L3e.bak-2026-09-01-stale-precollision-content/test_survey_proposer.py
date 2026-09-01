import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "web"))

from backend.survey_proposer import SurveyProposalError, parse_survey_proposal, propose_survey_concept


def _valid_raw():
    return """Here is my proposal:
    {
      "title": "Cloud Migration Risk Weighting",
      "description": "Weighs the criteria that matter most when deciding whether to migrate a legacy system to the cloud.",
      "instrument": "bwm",
      "instrument_justification": "Five criteria is a moderate count; BWM is efficient here and doesn't need pairwise coverage.",
      "criteria": [
        {"code": "COST", "label": "Migration cost"},
        {"code": "SEC", "label": "Security posture"},
        {"code": "DOWN", "label": "Downtime risk"},
        {"code": "SKILL", "label": "Team skill fit"},
        {"code": "VEND", "label": "Vendor lock-in"}
      ]
    }
    Let me know if you'd like changes.
    """


def test_parses_a_well_formed_proposal():
    result = parse_survey_proposal(_valid_raw())
    assert result["title"] == "Cloud Migration Risk Weighting"
    assert result["instrument"] == "bwm"
    assert len(result["criteria"]) == 5
    assert result["criteria"][0]["code"] == "COST"


def test_rejects_no_json_object():
    with pytest.raises(SurveyProposalError):
        parse_survey_proposal("Sorry, I can't help with that.")


def test_rejects_malformed_json():
    with pytest.raises(SurveyProposalError):
        parse_survey_proposal("{\"title\": oops}")


def test_rejects_missing_required_field():
    import json

    data = json.loads(_valid_raw().split("Here is my proposal:")[1].rsplit("Let me", 1)[0])
    del data["instrument_justification"]
    with pytest.raises(SurveyProposalError, match="instrument_justification"):
        parse_survey_proposal(json.dumps(data))


def test_rejects_an_unknown_instrument():
    raw = """{
      "title": "T", "description": "D", "instrument": "delphi",
      "instrument_justification": "J", "criteria": [{"code": "A", "label": "A"}]
    }"""
    with pytest.raises(SurveyProposalError, match="delphi"):
        parse_survey_proposal(raw)


def test_rejects_duplicate_criterion_codes():
    raw = """{
      "title": "T", "description": "D", "instrument": "bwm", "instrument_justification": "J",
      "criteria": [{"code": "A", "label": "First"}, {"code": "A", "label": "Second"}]
    }"""
    with pytest.raises(SurveyProposalError, match="unique"):
        parse_survey_proposal(raw)


def test_rejects_empty_criteria_list():
    raw = """{
      "title": "T", "description": "D", "instrument": "bwm", "instrument_justification": "J",
      "criteria": []
    }"""
    with pytest.raises(SurveyProposalError):
        parse_survey_proposal(raw)


def test_propose_survey_concept_calls_the_provider_and_parses_its_response(monkeypatch):
    class _FakeProvider:
        def complete(self, messages, *, model, temperature, max_tokens, top_p=1.0, seed=None, **extra):
            class _R:
                text = _valid_raw()

            return _R()

    import symphysis.providers as providers_module

    monkeypatch.setattr(providers_module, "get_provider", lambda name: _FakeProvider())
    result = propose_survey_concept("A study about cloud migration risk.", "ollama", "mistral:7b")
    assert result["title"] == "Cloud Migration Risk Weighting"
