# Tasks

Dan annotates an item directly with a line beginning `DAN:` underneath it;
that annotation is an instruction, work the item the way he answered it
there, not as commentary to re-litigate.

## Pipeline stages: remaining subagent queue

`spawning/pipeline.py` (landed 2026-09-06) has `setup_review` and
`response_review` as the first two stages. Dan asked for the full taxonomy
of subagents this pipeline should eventually cover; each remaining item
below is its own PR-sized slice (new meta-`Instrument` + card template),
same shape as the first two: see `docs/development/changelog.md`'s
2026-09-06 entry and the README's "Pipeline stages" section for the pattern
to follow. Priority order, highest leverage first:

1. **Rejection/skip diagnostician**: turns `orchestrator.py`'s raw
   `skipped_notices`/`pending_notices` exception strings into a synthesized
   diagnosis (model incapability vs. prompt design flaw vs. infra/hardware
   failure vs. guardrail-too-strict). Cheapest to build: the raw data
   already exists in `run_survey()`.
2. **Trust/provenance auditor**: walks `conversation.jsonl` +
   `spawn_declaration.json` + the integrity manifest per agent, confirms
   the trace is a complete, internally consistent story (no missing
   `raw_completion`, no capability escalation across a spawn chain, no
   orphaned claimed source). Directly serves this project's own "No
   Fabricated Results" mandate (see root `CLAUDE.md`); highest-leverage
   item on this list.
3. **Bias-detection agent**: correlated dimension-favoritism across
   agents independent of role, ordering/anchoring effects, suspiciously
   identical reasoning suggesting insufficient real panel diversity. Dan's
   explicit ask.
4. **Instrument-design critic**: methodological review of the BWM/AHP/
   hierarchical structure itself (too many criteria per level, ambiguous
   or overlapping dimension labels), pre-run.
5. **Panel-diversity / correlated-bias pre-check**: reviews the
   configured panel before a run for correlated-bias risk (same
   model+temperature+prompt across "independent" agents).
6. **Human-AI combination sanity-checker** (HAWC-BWM specific): flags
   suspicious divergence between human and agent panels before it's
   presented as combined.
7. **Capability/lineage auditor**: confirms every spawn's granted
   capabilities are a genuine subset of its parent's across the whole
   lineage tree, once child-spawning sees more real use than the two
   current stages.
8. **Report-narrator**: executive-summary prose strictly grounded in
   already-solved numbers, layered onto the existing deterministic
   `reporting.py`.

DAN: confirm order/scope before starting #1, or reorder if a different one
matters more once setup_review/response_review have seen real use.

## Result provenance and watermarking (plan only, not started)

Dan asked (2026-09-06) for a plan covering two related but distinct goals:
LLM output watermarking so a claimed AI-panel response cannot be faked, and
a verification mechanism so anyone can check whether a given survey's
results genuinely came from this tool and were not deliberately altered
afterward. See `docs/architecture/provenance-and-watermarking-plan.md` for
the full plan (threat model, two-layer design, phased task list); this
entry just tracks that the plan exists and nothing under it has been built
yet.

DAN: review the plan doc and confirm which phase to start with; Phase A
(generation-time attestation signing) is buildable now with existing
identity/credential infrastructure, Phase B (real statistical text
watermarking) is a research-gated, provider-dependent investment that
needs a scoping decision before any code is written.
