"""End-to-end orchestrator test using the real, complete 7-level
TrustRouter hierarchy (see trustrouter.py in the TrustRouter survey-app
for the authoritative structure this mirrors), driven by manual-provider
agents with pre-seeded responses so no live model call is needed."""

import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from symphysis.agent_card import GuardrailsSpec, ModelSpec, PermissionsSpec, RagSpec, SamplingSpec, new_card
from symphysis.config import load_survey_config
from symphysis.orchestrator import run_survey

LEVELS = [
    {
        "id": "L1", "name": "Top-level TrustRouter factors",
        "description": "The four expert-weighted factors of TrustRouter = DVS x F x (1+E) x A.",
        "dimensions": ["DVS", "F", "E", "A"],
        "dimension_labels": {"DVS": "Data Value Score", "F": "Technical Feasibility Fit", "E": "Economic Value", "A": "Attack Resistance"},
    },
    {
        "id": "L2", "name": "Six trust dimensions inside DVS", "description": "The six trust lenses making up DVS.",
        "dimensions": ["Q", "PT", "V", "IC", "L", "C"],
        "dimension_labels": {"Q": "Quality", "PT": "Provenance Trust", "V": "Verification Strength", "IC": "Independent Confirmation", "L": "Legal Compliance", "C": "Criticality"},
        "parent_level": "L1", "parent_criterion": "DVS",
    },
    {
        "id": "L3a", "name": "Quality clusters (ISO 25012)", "description": "ISO 25012 quality clusters.",
        "dimensions": ["IQ", "CQ", "RQ"],
        "dimension_labels": {"IQ": "Intrinsic Quality", "CQ": "Contextual Quality", "RQ": "Representational Quality"},
        "parent_level": "L2", "parent_criterion": "Q",
    },
    {
        "id": "L3b", "name": "Provenance Trust sub-parts", "description": "Trusting where data came from.",
        "dimensions": ["T_source", "T_chain", "T_history"],
        "dimension_labels": {"T_source": "Source credentials", "T_chain": "Custody chain", "T_history": "Historical track record"},
        "parent_level": "L2", "parent_criterion": "PT",
    },
    {
        "id": "L3c", "name": "Verification Strength sub-parts", "description": "Evidence backing the data.",
        "dimensions": ["V_crypto", "V_audit", "V_diversity"],
        "dimension_labels": {"V_crypto": "Cryptographic evidence", "V_audit": "Audit trail completeness", "V_diversity": "Diversity of verification sources"},
        "parent_level": "L2", "parent_criterion": "V",
    },
    {
        "id": "L3d", "name": "Attack Resistance sub-parts", "description": "How hard it is to cheat with this data.",
        "dimensions": ["A_sybil", "A_oracle", "A_insider"],
        "dimension_labels": {"A_sybil": "Sybil resistance", "A_oracle": "Oracle resistance", "A_insider": "Insider resistance"},
        "parent_level": "L1", "parent_criterion": "A",
    },
    {
        "id": "L3e", "name": "Economic Value sub-parts", "description": "Could someone pay to access this data.",
        "dimensions": ["E_market", "E_liquidity", "E_demand"],
        "dimension_labels": {"E_market": "Current marketplace demand", "E_liquidity": "Tokenisation ease", "E_demand": "Future demand"},
        "parent_level": "L1", "parent_criterion": "E",
    },
]


def _write_prompt_template(config_dir: Path) -> Path:
    path = config_dir / "system_prompt.txt"
    path.write_text("Role: {role}\n{role_description}\n", encoding="utf-8")
    return path


def _write_survey(survey_dir: Path) -> None:
    (survey_dir / "agents").mkdir(parents=True, exist_ok=True)
    survey_yaml = {
        "id": "trustrouter-hierarchical-test",
        "title": "TrustRouter hierarchical test",
        "instrument": "hierarchical_bwm",
        "instrument_params": {
            "composite_formula": "TrustRouter = DVS x F x (1 + E) x A",
            "levels": LEVELS,
        },
        "weighting": {},
    }
    (survey_dir / "survey.yaml").write_text(yaml.dump(survey_yaml, sort_keys=False), encoding="utf-8")


def _level_answer(codes, best, worst):
    return {
        "best": best,
        "worst": worst,
        "best_to_others": {c: (1 if c == best else 3) for c in codes},
        "others_to_worst": {c: (1 if c == worst else 3) for c in codes},
        "reasoning": f"{best} is most important, {worst} is least important in this level.",
    }


def _add_manual_agent(survey_dir: Path, agent_id: str, prompt_template: Path) -> None:
    card = new_card(
        agent_id=agent_id,
        role="Blockchain Trust Specialist",
        role_description="A specialist in distributed trust systems.",
        system_prompt_template=str(prompt_template),
        model=ModelSpec(provider="manual", name="gemini-2.5-pro"),
        rag=RagSpec(enabled=False),
        sampling=SamplingSpec(repeats=1, max_retries_on_malformed=0),
        permissions=PermissionsSpec(allowed_providers=["manual"]),
        guardrails=GuardrailsSpec(),
        did_seed="test-seed",
    )
    card.write(survey_dir / "agents" / f"{agent_id}.json")

    payload = {
        "levels": {
            "L1": _level_answer(["DVS", "F", "E", "A"], "DVS", "F"),
            "L2": _level_answer(["Q", "PT", "V", "IC", "L", "C"], "C", "IC"),
            "L3a": _level_answer(["IQ", "CQ", "RQ"], "CQ", "RQ"),
            "L3b": _level_answer(["T_source", "T_chain", "T_history"], "T_source", "T_history"),
            "L3c": _level_answer(["V_crypto", "V_audit", "V_diversity"], "V_audit", "V_diversity"),
            "L3d": _level_answer(["A_sybil", "A_oracle", "A_insider"], "A_oracle", "A_insider"),
            "L3e": _level_answer(["E_market", "E_liquidity", "E_demand"], "E_market", "E_liquidity"),
        },
        "sources_used": ["general_knowledge"],
    }

    manual_dir = survey_dir / "agents" / agent_id / "manual_input"
    manual_dir.mkdir(parents=True)
    (manual_dir / "prompt_00.md").write_text("prompt", encoding="utf-8")
    (manual_dir / "response_00.txt").write_text(json.dumps(payload), encoding="utf-8")


def test_full_trustrouter_hierarchy_runs_end_to_end(tmp_path):
    survey_dir = tmp_path / "trustrouter-hierarchical-test"
    _write_survey(survey_dir)
    prompt_template = _write_prompt_template(tmp_path)
    _add_manual_agent(survey_dir, "agent-one", prompt_template)

    survey = load_survey_config(survey_dir)
    result = run_survey(survey)

    assert result["instrument"] == "hierarchical_bwm"
    assert set(result["agent_panel"]["levels"].keys()) == {"L1", "L2", "L3a", "L3b", "L3c", "L3d", "L3e"}

    global_weights = result["agent_panel"]["global_weights"]
    expected_leaves = {
        "F", "IC", "L", "C",
        "IQ", "CQ", "RQ", "T_source", "T_chain", "T_history",
        "V_crypto", "V_audit", "V_diversity",
        "A_sybil", "A_oracle", "A_insider",
        "E_market", "E_liquidity", "E_demand",
    }
    assert set(global_weights.keys()) == expected_leaves
    for elaborated in ("DVS", "Q", "PT", "V", "E", "A"):
        assert elaborated not in global_weights

    assert len(result["agent_panel"]["populated_equations"]) == 6  # DVS, Q, PT, V, A, E

    report_text = (survey_dir / "report" / "report.md").read_text(encoding="utf-8")
    assert "TrustRouter = DVS x F x (1 + E) x A" in report_text
    assert "## Global leaf weights" in report_text
    assert "## Populated equations" in report_text
    assert "## Methodology" in report_text
    assert "## Per-agent detail" in report_text
    assert "[L1]" in report_text  # per-level reasoning concatenation
    assert "[L3e]" in report_text

    manifest_path = survey_dir / "integrity_manifest.json"
    assert manifest_path.exists()
