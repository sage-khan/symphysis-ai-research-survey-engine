"""Build a one-agent pilot survey proving the "bwm_two_stage" OpenManus flow
(runtime/_openmanus_driver.py::_run_bwm_two_stage, wired in 2026-09-01) works
end-to-end through the real Symphysis engine, not just an isolated scratch
script: real survey.yaml/rulefile.md/knowledge_repo, a real agent card with
runtime_backend="openmanus", run via `symphysis run`, producing the same
result.json/conversation.jsonl/report.md output shape as any other survey.

Reuses the real L1 TrustRouter dimensions (survey.yaml, rulefile.md,
knowledge_repo/) from the trustrouter-hawc-bwm-slm-run1-2026-09-01-L1 survey
(Run 1's baseline, direct_completion backend) so this pilot answers the
SAME real elicitation task, just through the agentic backend instead.

See docs/research/.../00-trustrouter/symphysis-planning/
agentic-experiment-design-decisions.md (project-veritas) for why this flow
exists: a single tool call combining reasoning and structured submission
proved fragile for mistral:7b; a second LLM-based formatter call introduced
its own fabrication/reshuffling failure; the two-turn deterministic design
here was validated in isolation (5/5 across 25 individual values) before
being wired into the production runtime.

Run:
    cd /path/to/symphysis-ai-research-survey-engine
    python3 scripts/build_trustrouter_agentic_two_stage_pilot.py
"""

from __future__ import annotations

import shutil
from pathlib import Path

import yaml

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from symphysis.agent_card import ModelSpec, RagSpec, SamplingSpec, PermissionsSpec, GuardrailsSpec, new_card

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_SURVEY = REPO_ROOT / "surveys" / "trustrouter-hawc-bwm-slm-run1-2026-09-01-L1"
SURVEY_ID = "trustrouter-agentic-two-stage-pilot-2026-09-01"
MODEL_NAME = "mistral:7b"

ROLE_SLUG = "blockchain-engineer"
ROLE_NAME = "Blockchain / DLT Engineer"
ROLE_DESCRIPTION = (
    "A blockchain/DLT engineer with production experience on permissioned-ledger deployments, "
    "responsible for evaluating technical feasibility, throughput, and tamper-evidence guarantees."
)

RULEFILE_TEXT = """# Survey rules: TrustRouter Agentic Two-Stage Pilot (2026-09-01)

This is a **pilot run** proving the OpenManus-backed "bwm_two_stage" runtime flow end-to-end
through the real Symphysis engine (`symphysis run`), not an isolated test script. One agent,
one level (L1, the four top-level TrustRouter factors), `runtime_backend: openmanus`.

**Why this flow exists (do not "helpfully" answer differently):** asking mistral:7b to combine
free-text reasoning and a structured tool-call submission in one turn proved fragile (see this
repo's docs/development/diagnostics.md and project-veritas's
agentic-experiment-design-decisions.md, 2026-09-01 entries). This survey's agent instead
answers via two plain completions driven by the runtime itself (best/worst, then dynamically
built pairwise ratings) -- no tool call is issued for this instrument.

**This survey's level: L1 -- Top-level TrustRouter factors.**
The four top-level TrustRouter factors (DVS, F, E, A), combined multiplicatively as
TrustRouter = DVS x F x (1+E) x A. This comparison expresses relative importance among
multiplicatively-combined factors, not a share of one linear total.

Comparison set for this survey:
- **DVS** (Data Value Score): Composite trustworthiness of the data.
- **F** (Technical Feasibility Fit): How well the artefact fits ledger constraints (size,
  update rate, latency). F = 1 - P.
- **E** (Economic Value): Financial or asset value at stake if the data is corrupted or lost.
- **A** (Attack Resistance): Difficulty of undetected manipulation.

## Grounding rules

1. Ground every comparison in what each criterion specifically means for a construction-project
   record considered for blockchain storage. See this survey's shared knowledge repository
   (`knowledge_repo/`) for the real survey instrument's canonical glossary, the concept-paper
   primer, and the research hypothesis this elicitation exists to test.
2. TrustRouter's composite combines its top-level factors multiplicatively
   (`TrustRouter = DVS x F x (1 + E) x A`), not as a weighted sum.
3. Do not treat any one criterion as self-evidently more important than the others by default.
4. Answer as the professional you are configured to be would, on the merits of these criteria
   as construction-project data-trust factors.
5. Cite only real, verifiable, reputable sources. Never cite or imply reliance on a blog,
   forum, or marketing page.
"""


def main() -> None:
    survey_dir = REPO_ROOT / "surveys" / SURVEY_ID
    agents_dir = survey_dir / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    (survey_dir / "knowledge_repo").mkdir(parents=True, exist_ok=True)

    source_yaml = yaml.safe_load((SOURCE_SURVEY / "survey.yaml").read_text(encoding="utf-8"))
    survey_yaml = {
        "id": SURVEY_ID,
        "title": f"TrustRouter Agentic Two-Stage Pilot ({MODEL_NAME}) -- Level L1",
        "description": (
            "One-agent pilot proving the OpenManus-backed bwm_two_stage runtime flow end-to-end "
            "through the real Symphysis engine. Same L1 dimensions as the "
            "trustrouter-hawc-bwm-slm-run1-2026-09-01-L1 baseline survey, answered via the "
            "agentic (runtime_backend=openmanus) backend instead of direct_completion."
        ),
        "instrument": "bwm",
        "instrument_params": source_yaml["instrument_params"],
        "created_at": "2026-09-01T00:00:00+00:00",
    }
    (survey_dir / "survey.yaml").write_text(
        yaml.safe_dump(survey_yaml, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )
    (survey_dir / "rulefile.md").write_text(RULEFILE_TEXT, encoding="utf-8")

    for src in (SOURCE_SURVEY / "knowledge_repo").glob("*.md"):
        shutil.copy2(src, survey_dir / "knowledge_repo" / src.name)

    agent_id = f"{ROLE_SLUG}-openmanus-ollama"
    card = new_card(
        agent_id=agent_id,
        role=ROLE_NAME,
        role_description=ROLE_DESCRIPTION,
        system_prompt_template="config/prompts/expert_panel_system.txt",
        model=ModelSpec(
            provider="ollama",
            name=MODEL_NAME,
            temperature=0.3,
            max_tokens=4096,
            top_p=1.0,
            seed=42,
        ),
        instrument="bwm",
        rag=RagSpec(enabled=False, corpus_path=None),
        sampling=SamplingSpec(repeats=2, max_retries_on_malformed=2, agreement_threshold=0.0),
        permissions=PermissionsSpec(data_scopes=[], allowed_providers=["ollama"]),
        guardrails=GuardrailsSpec(
            schema_validation=True,
            denylist_patterns=[
                r"ignore (all|any|the) (previous|prior|above) instructions",
                r"sk-[A-Za-z0-9]{20,}",
                r"-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----",
            ],
        ),
        deterministic_did=True,
        did_seed=SURVEY_ID,
        runtime_backend="openmanus",
    )
    card.write(agents_dir / f"{agent_id}.json")

    print(f"Built {survey_dir} with 1 agent card ({agent_id}, runtime_backend=openmanus, model={MODEL_NAME})")


if __name__ == "__main__":
    main()
