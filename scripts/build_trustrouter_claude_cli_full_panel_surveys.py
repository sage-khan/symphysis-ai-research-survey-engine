"""Generate the 7 per-level flat-BWM survey folders for the TrustRouter
CLAUDE CLI Panel (Phase 3): same 7-level split, same 6 construction-role
personas x base/RAG, same real dimensions/labels/descriptions/knowledge_repo/
RAG corpora as Phase 1 (mistral:7b, agentic/openmanus) and Phase 2 (qwen3/
phi4/llama3.1, agentic/openmanus) -- but every agent card here uses
provider="claude_cli" and runtime_backend="direct_completion" instead:
Claude models are reliable enough at single-shot structured JSON output that
the two-turn bwm_two_stage workaround built for small local models (see
agentic-experiment-design-decisions.md) is unnecessary here. Each agent's
single instrument="bwm" call goes straight through ClaudeCliProvider, which
shells out to the locally-authenticated `claude` CLI (see
src/symphysis/providers/claude_cli_provider.py's module docstring for the
full rationale -- no ANTHROPIC_API_KEY needed or used).

See docs/research/.../00-trustrouter/symphysis-planning/
agentic-experiment-design-decisions.md's Phase 3 entry (project-veritas) for
the scope decision (Haiku + Sonnet; Opus dropped after a real per-call cost
measurement made it the clear majority of the estimated spend).

Run (pass the `claude` CLI's own model alias and a filesystem-safe slug):
    cd /path/to/symphysis-ai-research-survey-engine
    python3 scripts/build_trustrouter_claude_cli_full_panel_surveys.py haiku claude-haiku
    python3 scripts/build_trustrouter_claude_cli_full_panel_surveys.py sonnet claude-sonnet

Each invocation builds its own 7 survey folders under
surveys/trustrouter-claude-cli-full-panel-<slug>-2026-09-01-<level_id>/.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from symphysis.agent_card import ModelSpec, RagSpec, SamplingSpec, PermissionsSpec, GuardrailsSpec, new_card

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_SURVEY = REPO_ROOT / "surveys" / "trustrouter-hawc-bwm"

MODEL_NAME = sys.argv[1] if len(sys.argv) > 1 else "haiku"
MODEL_SLUG = sys.argv[2] if len(sys.argv) > 2 else "claude-haiku"
PARENT_RUN_ID = f"trustrouter-claude-cli-full-panel-{MODEL_SLUG}-2026-09-01"
DID_SEED = PARENT_RUN_ID

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

RULEFILE_TEMPLATE = """# Survey rules: TrustRouter Claude CLI Panel -- Level {level_id} ({level_name})

This survey is **one of 7 sibling surveys** that together make up the TrustRouter Claude CLI
Panel run (model: {model_name}, provider: claude_cli, runtime_backend: direct_completion). Each
level runs as its own independent, single-comparison-set survey, answered via a single
structured-JSON completion (the flat "bwm" instrument), not the two-turn agentic flow used for
the local SLM phases.

**This survey's own level: {level_id} -- {level_name}.**
{level_context}

Comparison set for this survey:
{dimension_list}

## Grounding rules (apply to every level, copied from the parent hierarchy survey)

1. Ground every comparison in what each criterion specifically means for a
   construction-project record considered for blockchain storage. See this
   survey's shared knowledge repository (`knowledge_repo/`) for the real
   survey instrument's canonical glossary, the concept-paper primer, and the
   research hypothesis this elicitation exists to test.
2. TrustRouter's composite combines its top-level factors multiplicatively
   (`TrustRouter = DVS x F x (1 + E) x A`), not as a weighted sum -- see the
   concept-paper primer before answering L1 specifically.
3. Do not treat any one criterion as self-evidently more important than the
   others by default.
4. Answer as the professional you are configured to be would, on the merits
   of these criteria as construction-project data-trust factors.
5. Ground your Best/Worst choice and ratings in any reference material you
   were given, citing it by its exact tag where possible.
6. Cite only real, verifiable, reputable sources. Never cite or imply
   reliance on a blog, forum, or marketing page.
"""

LEVEL_CONTEXT = {
    "L1": "The four top-level TrustRouter factors (DVS, F, E, A), combined "
          "multiplicatively as TrustRouter = DVS x F x (1+E) x A.",
    "L2": "The six trust dimensions that make up the Data Value Score (DVS) factor from L1.",
    "L3a": "The three ISO 25012 quality clusters that decompose Quality (Q) from L2.",
    "L3b": "The three sub-parts that decompose Provenance Trust (PT) from L2.",
    "L3c": "The three sub-parts that decompose Verification Strength (V) from L2.",
    "L3d": "The three sub-parts that decompose Attack Resistance (A) from L1.",
    "L3e": "The three sub-parts that decompose Economic Value (E) from L1.",
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
        "title": f"TrustRouter Claude CLI Panel ({MODEL_NAME}) -- Level {level_id}: {level['name']}",
        "description": (
            f"One of 7 sibling per-level surveys (parent run: {PARENT_RUN_ID}). "
            f"{level['description']} Uses the flat bwm instrument answered via a single "
            f"structured-JSON completion (provider=claude_cli, runtime_backend=direct_completion)."
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
            agent_id = f"{role_slug}-{variant}-claude"
            rag_enabled = variant == "rag"
            corpus_path = f"surveys/trustrouter-hawc-bwm/rag_corpora/{role_slug}"
            card = new_card(
                agent_id=agent_id,
                role=role_name,
                role_description=role_description,
                system_prompt_template="config/prompts/expert_panel_system.txt",
                model=ModelSpec(
                    provider="claude_cli",
                    name=MODEL_NAME,
                    temperature=0.3,
                    max_tokens=4096,
                    top_p=1.0,
                    seed=None,
                ),
                instrument="bwm",
                rag=RagSpec(
                    enabled=rag_enabled,
                    corpus_path=corpus_path if rag_enabled else None,
                ),
                sampling=SamplingSpec(repeats=3, max_retries_on_malformed=2, agreement_threshold=0.0),
                permissions=PermissionsSpec(
                    data_scopes=[f"{corpus_path}/**"] if rag_enabled else [],
                    allowed_providers=["claude_cli"],
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
