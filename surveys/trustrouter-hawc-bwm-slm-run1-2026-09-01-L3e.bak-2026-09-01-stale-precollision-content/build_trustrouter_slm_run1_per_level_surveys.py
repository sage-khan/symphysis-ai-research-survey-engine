"""Generate the 7 per-level flat-BWM survey folders for the TrustRouter
SLM Panel Run 1 (2026-09-01).

Why per-level, not the existing hierarchical_bwm-in-one-shot survey
(trustrouter-hawc-bwm): docs/development/diagnostics.md's "Every small/mid
local Ollama model failed the full seven-level hierarchical_bwm task" and
its follow-on entries found that asking a 7B-32B local model to answer all
seven BWM levels (up to 24 criteria) in one completion produces missing
keys, self-rating convention errors, and truncation, independent of prompt
wording fixes already applied. The documented next escalation was "splitting
hierarchical_bwm into one call per level (matching the flat bwm
instrument's proven-reliable single-level shape)" -- this script does
exactly that: one standalone `bwm`-instrument survey per level, each with
its own single comparison set, run independently.

Each of the 6 construction-role personas (base + RAG = 12 agents) keeps the
SAME deterministic DID across all 7 level-surveys (did_seed is the shared
parent run id, not the per-level survey id), so the 7 runs represent the
same synthetic expert answering 7 separate sections of one panel, not 7
unrelated agents.

Run:
    cd /path/to/symphysis-ai-research-survey-engine
    python3 scripts/build_trustrouter_slm_run1_per_level_surveys.py
"""

from __future__ import annotations

import shutil
from pathlib import Path

import yaml

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from symphysis.agent_card import ModelSpec, RagSpec, SamplingSpec, PermissionsSpec, GuardrailsSpec, new_card

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_SURVEY = REPO_ROOT / "surveys" / "trustrouter-hawc-bwm"
PARENT_RUN_ID = "trustrouter-hawc-bwm-slm-run1-2026-09-01"
MODEL_NAME = "qwen3:14b"
DID_SEED = PARENT_RUN_ID  # shared across all 7 level-surveys: same synthetic expert identity throughout

ROLES = [
    ("bim-coordinator", "BIM Coordinator",
     "A BIM coordinator with 10+ years managing multi-stakeholder Building Information Models "
     "on renovation and new-build projects, responsible for model federation, clash detection, "
     "and lifecycle documentation."),
    ("blockchain-engineer", "Blockchain / DLT Engineer",
     "A blockchain/DLT engineer with production experience on permissioned-ledger deployments, "
     "responsible for evaluating technical feasibility, throughput, and tamper-evidence guarantees."),
    ("compliance-officer", "Compliance and Regulatory Officer",
     "A facility-management compliance officer responsible for GDPR and construction-regulatory "
     "obligations across a building's operational lifecycle."),
    ("data-engineer", "Data Engineering Specialist",
     "A data engineering specialist responsible for data quality pipelines, provenance tracking, "
     "and polyglot-persistence routing decisions on construction-project datasets."),
    ("project-manager", "Construction Project Manager",
     "A construction project manager responsible for coordinating multi-stakeholder documentation "
     "flows across a renovation or new-build project's full lifecycle."),
    ("structural-engineer", "Structural Engineer",
     "A chartered structural engineer responsible for structural-capacity dossiers and their "
     "downstream reliance by insurers, regulators, and building owners over decades."),
]

RULEFILE_TEMPLATE = """# Survey rules: TrustRouter SLM Panel Run 1 -- Level {level_id} ({level_name})

This survey is **one of 7 sibling surveys** that together make up the
TrustRouter SLM Panel Run 1 (2026-09-01, model: {model_name}). The full
TrustRouter Best-Worst-Method elicitation has 7 comparison levels (L1, L2,
L3a-L3e); each level is run here as its **own independent, single-comparison-set
survey** rather than bundling all 7 into one completion.

**Why split this way (do not "helpfully" answer other levels):** local
models in the 7B-32B range reliably fail when asked to answer all 7 BWM
levels (up to 24 criteria) in a single completion -- missing criteria,
self-rating convention errors ("Best vs Best" rated 9 instead of 1), and
truncation. See this repo's docs/development/diagnostics.md for the full,
documented history of that failure mode. Splitting into one call per level
(this survey) reuses the already-proven-reliable single-level `bwm`
instrument shape instead.

**This survey's own level: {level_id} -- {level_name}.**
{level_context}

Comparison set for this survey:
{dimension_list}

## Grounding rules (apply to every level, copied from the parent hierarchy survey)

1. Ground every comparison in what each criterion specifically means for a
   construction-project record considered for blockchain storage. See this
   survey's shared knowledge repository (`knowledge_repo/`) for the real
   survey instrument's canonical glossary, the concept-paper primer, and the
   research hypothesis this elicitation exists to test -- these are the
   ground truth for terminology, not a paraphrase.
2. TrustRouter's composite combines its top-level factors multiplicatively
   (`TrustRouter = DVS x F x (1 + E) x A`), not as a weighted sum -- see the
   concept-paper primer before answering L1 specifically.
3. Do not treat any one criterion as self-evidently more important than the
   others by default. Surface genuine professional judgement, not an
   assumed "obviously correct" ranking.
4. Answer as the professional you are configured to be would, on the merits
   of these criteria as construction-project data-trust factors.
5. Ground your Best/Worst choice and ratings in any reference material you
   were given (shared knowledge repository, your role's RAG corpus), citing
   it by its exact tag. If you were not given material for a specific
   point, reason from your own domain expertise and say so plainly.
6. Cite only real, verifiable, reputable sources (peer-reviewed papers,
   labelled preprints, standards documents, academic/institutional
   technical reports). Never cite or imply reliance on a blog, forum, or
   marketing page.
7. The Best-to-Others and Others-to-Worst ratings are RATIOS, not
   importance scores: Best compared to itself is always exactly 1 (one time
   as important as itself), never 9; the same applies to Worst compared to
   itself.
"""

LEVEL_CONTEXT = {
    "L1": "The four top-level TrustRouter factors (DVS, F, E, A), combined "
          "multiplicatively as TrustRouter = DVS x F x (1+E) x A. This comparison expresses "
          "relative importance among multiplicatively-combined factors, not a share of one "
          "linear total.",
    "L2": "The six trust dimensions that make up the Data Value Score (DVS) factor from L1. "
          "These six weights, once aggregated, determine how DVS itself is computed as a "
          "weighted combination of Quality, Provenance Trust, Verification Strength, "
          "Independent Confirmation, Legal Compliance, and Criticality.",
    "L3a": "The three ISO 25012 quality clusters that decompose Quality (Q) from L2 into "
           "Intrinsic, Contextual, and Representational quality.",
    "L3b": "The three sub-parts that decompose Provenance Trust (PT) from L2: source "
           "credentials, custody chain, and historical track record.",
    "L3c": "The three sub-parts that decompose Verification Strength (V) from L2: "
           "cryptographic evidence, audit-trail completeness, and diversity of verification "
           "sources.",
    "L3d": "The three sub-parts that decompose Attack Resistance (A) from L1: Sybil "
           "resistance, oracle resistance, and insider resistance.",
    "L3e": "The three sub-parts that decompose Economic Value (E) from L1: current "
           "marketplace demand, tokenisation/liquidity ease, and projected future demand.",
}


def build_level_survey(level: dict) -> None:
    level_id = level["id"]
    survey_id = f"{PARENT_RUN_ID}-{level_id}"
    survey_dir = REPO_ROOT / "surveys" / survey_id
    agents_dir = survey_dir / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    (survey_dir / "knowledge_repo").mkdir(parents=True, exist_ok=True)

    dims = level["dimensions"]
    labels = level.get("dimension_labels", {})
    descs = level.get("dimension_descriptions", {})

    survey_yaml = {
        "id": survey_id,
        "title": f"TrustRouter SLM Panel Run 1 ({MODEL_NAME}) -- Level {level_id}: {level['name']}",
        "description": (
            f"One of 7 sibling per-level surveys (parent run: {PARENT_RUN_ID}). "
            f"{level['description']} Uses the flat bwm instrument (single comparison set), "
            f"not hierarchical_bwm, per the per-level context-splitting design documented in "
            f"this survey's rulefile.md."
        ),
        "instrument": "bwm",
        "instrument_params": {
            "dimensions": dims,
            "dimension_labels": labels,
            "dimension_descriptions": descs,
        },
        "created_at": "2026-09-01T00:00:00+00:00",
    }
    (survey_dir / "survey.yaml").write_text(
        yaml.safe_dump(survey_yaml, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )

    dimension_list_md = "\n".join(
        f"- **{code}** ({labels.get(code, code)}): {descs.get(code, '')}" for code in dims
    )
    rulefile_text = RULEFILE_TEMPLATE.format(
        level_id=level_id,
        level_name=level["name"],
        model_name=MODEL_NAME,
        level_context=LEVEL_CONTEXT.get(level_id, level["description"]),
        dimension_list=dimension_list_md,
    )
    (survey_dir / "rulefile.md").write_text(rulefile_text, encoding="utf-8")

    for src in (SOURCE_SURVEY / "knowledge_repo").glob("*.md"):
        shutil.copy2(src, survey_dir / "knowledge_repo" / src.name)

    for role_slug, role_name, role_description in ROLES:
        for variant in ("base", "rag"):
            agent_id = f"{role_slug}-{variant}-ollama"
            rag_enabled = variant == "rag"
            corpus_path = f"surveys/trustrouter-hawc-bwm/rag_corpora/{role_slug}"
            card = new_card(
                agent_id=agent_id,
                role=role_name,
                role_description=role_description,
                system_prompt_template="config/prompts/expert_panel_system.txt",
                model=ModelSpec(
                    provider="ollama",
                    name=MODEL_NAME,
                    temperature=0.7,
                    max_tokens=4096,
                    top_p=1.0,
                    seed=42,
                ),
                instrument="bwm",
                rag=RagSpec(
                    enabled=rag_enabled,
                    corpus_path=corpus_path if rag_enabled else None,
                ),
                sampling=SamplingSpec(repeats=5, max_retries_on_malformed=2, agreement_threshold=0.0),
                permissions=PermissionsSpec(
                    data_scopes=[f"{corpus_path}/**"] if rag_enabled else [],
                    allowed_providers=["ollama"],
                ),
                guardrails=GuardrailsSpec(
                    schema_validation=True,
                    denylist_patterns=[
                        r"ignore (all|any|the) (previous|prior|above) instructions",
                        r"sk-[A-Za-z0-9]{20,}",
                        r"-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----",
                    ],
                ),
                deterministic_did=True,
                did_seed=DID_SEED,
                runtime_backend="direct_completion",
            )
            card.write(agents_dir / f"{agent_id}.json")

    print(f"Built {survey_dir} ({len(dims)} criteria: {', '.join(dims)}) with {len(ROLES) * 2} agent cards")


def main() -> None:
    source_yaml = yaml.safe_load((SOURCE_SURVEY / "survey.yaml").read_text(encoding="utf-8"))
    levels = source_yaml["instrument_params"]["levels"]
    for level in levels:
        build_level_survey(level)
    print(f"\nDone: {len(levels)} per-level survey folders built under surveys/{PARENT_RUN_ID}-<level_id>/")


if __name__ == "__main__":
    main()
