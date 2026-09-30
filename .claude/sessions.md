# Session Log

Newest entry first. See `.claude/tasks.md` for the live working list this
log tracks against, and `.claude/memory.md` for durable decisions that
don't need re-litigating in a future session.

---

## 2026-09-06: Pipeline stages, setup-review and response-review as real child spawns

Asked: whether to bring in an external agent-orchestration framework
(deepagents, OpenManus, scale-agentex, vllm agentic-api, a "DeepSeek
harness") for a planner-plus-specialized-subagents survey pipeline, and to
list every subagent this pipeline should eventually cover.

Found before writing anything: this branch already vendors OpenManus with
a real `PlanningFlow` (unused by this codebase, by design; see the plan
doc's own principle that domain logic never leaves Symphysis's own code),
and `spawning/spawn.py`'s `mint_child`/`declare_child` were already fully
built and tested but called by nothing outside their own test file (Phase
3 task 19 in `docs/architecture/governance-layer-and-runtime-backends-plan.md`,
explicitly deferred). Recommended against adopting any external framework
wholesale; recommended finishing task 19 instead, generalized past its
original per-instrument-level scope.

Built: `spawning/pipeline.py` (config-driven pipeline stages, `survey.yaml`'s
new `pipeline:` key), `instruments/setup_review.py` and
`instruments/response_review.py` (meta-instruments reusing `Agent.run()`'s
existing machinery), wired into `orchestrator.py` before/after the panel
loop, a new report section, tests (`test_pipeline.py`,
`test_setup_review_instrument.py`, `test_response_review_instrument.py`,
`test_config_pipeline.py`: 21 new, all passing; full suite re-run,
322 passed/0 regressions). README/changelog/plan-doc status all updated in
the same change per `documentation-maintenance.md`.

Full 10-item subagent taxonomy and priority queue for the remaining 8
stages recorded in `.claude/tasks.md`; Dan to confirm/reorder before #1
(rejection/skip diagnostician) starts.

Same session, follow-up ask: a plan for LLM output watermarking (so a
claimed AI-panel response cannot be faked) plus a mechanism to verify a
survey's results genuinely came from this tool and were not deliberately
altered afterward. Wrote `docs/architecture/provenance-and-watermarking-plan.md`
(threat model, two-layer design: generation-time attestation signing,
buildable now with the existing did:key/Verifiable Credential
infrastructure; real statistical text watermarking, research-gated and
provider-dependent, not yet scoped for a start date). Nothing under this
plan is built yet; tracked in `.claude/tasks.md`.

---

## 2026-08-19 — Session continuity system (sessions.md, memory.md, tasks.md)

Set up the same session-continuity pattern used in
`coder-with-vibes-taylor-francis` and `ec-council`, applied here for
consistency across Dan's repos: this file (`.claude/sessions.md`, dated
append-only log, read first when resuming, written before ending any
session or risky operation), `.claude/memory.md` (durable decisions, not a
diary), and `.claude/tasks.md` (live working list, annotated with `DAN:`
lines for Dan's own decisions, folded into `docs/development/changelog.md`
once emptied per this repo's own `documentation-maintenance.md`). All three
live under `.claude/`, not the repo root, matching `creator-flow`'s
placement (a cleaner root, not cluttered with internal working files).

**Still open:** none from this pass. `memory.md` and `tasks.md` are freshly
seeded and will need real entries as work actually happens.
