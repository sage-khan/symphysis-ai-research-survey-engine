# Governance layer + pluggable runtime backends: architecture plan

**Status:** Phases 0-1 fully implemented and tested (identity/policy/audit
extraction, capability model, declared+attenuated spawning, lineage).
Phase 2's foundation is implemented and tested: `runtime/base.py`,
`runtime/ollama.py` (direct-completion default backend), and
`runtime/openmanus.py`/`_openmanus_driver.py` (OpenManus vendored as a
pinned git submodule at `vendor/openmanus/`, driven as a subprocess under
an isolated `vendor/openmanus/.venv`). Not yet done: wiring
`OpenManusBackend` into `orchestrator.py`'s actual survey-run path (today's
runs still go through `Agent.run()`'s direct provider call, not through
`runtime/` at all — `spawn_declared`'s `runtime_backend` field says
`"direct_completion"` for exactly this reason), `tools/registry.py`/
`tools/proxy.py`, and Phases 3-6. Companion to
`target-pipeline-vision.drawio`/`.png` (see `architecture-overview.md`)
rather than a replacement for it: that diagram's Orchestration/AI-panel
layers are the vision this plan makes concrete at the module level. Read
`current-system-architecture.*` for what else is real today.

This plan is also the concrete implementation of one item already named in
this README's own "Status / what's deferred" section: "a full Cedar/OPA-style
policy evaluator for `permissions` (currently a direct glob/allowlist check,
not a general policy engine)." Everything below is that item, plus the agent
identity/spawning and pluggable-backend work it depends on.

---

## 1. What this is

One sentence: a portable, cryptographically identifiable, policy-constrained,
auditable agent runtime, where an agent can spawn another agent without ever
exceeding the authority it was itself granted.

Symphysis already has most of the primitives (did:key identity, hyperparameter
cards, a full trace/audit trail, schema-validating guardrails) but they are
scattered across a few tightly-coupled files (`agent_card.py`, `did_key.py`,
`storage.py`, `permissions.py`, `guardrails.py`, `agent.py`) and there is no
concept of one agent spawning another. This plan:

1. Reorganizes the existing, working code into a clean governance-layer
   package (`identity/`, `policy/`, `audit/`), changing structure, not
   behavior, first.
2. Adds the one genuinely new capability that does not exist anywhere in the
   current codebase: declared, attenuated, logged agent-to-agent spawning.
3. Adds a pluggable `runtime/` backend interface, with **OpenManus as the
   flagship backend** (verified: MIT, Python, native Ollama, 58,130
   stars/10,098 forks, and a `BaseAgent -> ReActAgent -> ToolCallAgent ->
   Manus` class hierarchy that already demonstrates the exact specialization
   pattern this plan needs via its own `SWEAgent`/`DataAnalysis` subclasses),
   and OpenCode registered behind the same interface for coding-heavy tasks
   outside the survey domain itself.
4. Adds model-tiering (local-first, cloud-escalation) and per-level
   instrument decomposition, both riding on the same runtime/policy/audit
   plumbing rather than being separate mechanisms.

## 2. Design principles (binding on every phase below)

- **Local-first stays the default.** Ollama is the primary, zero-marginal-cost
  path. Cloud APIs (OpenRouter, Gemini, Anthropic, etc., all already supported
  provider names in `AgentCard.model.provider`) are an explicit escalation, not
  a replacement. No task in this plan changes that default.
- **Every spawn is declared before it acts.** An agent's DID, parent DID (or
  `null` for a root/human-initiated spawn), granted capabilities, model, and
  hyperparameters are written to the audit trail as that agent's first event,
  the same way `run_qa_precheck` is already always the first `conversation.jsonl`
  entry today. No agent runs before its declaration is on disk.
- **A child can never exceed its parent's authority.** Every spawn computes
  `effective_capabilities = intersection(parent_capabilities, requested_capabilities)`,
  never a union. This is the actual security property behind "without escaping
  the authority that created them," not just a phrase.
- **Domain logic never leaves Symphysis's own code.** The Bayesian/BWM/AHP
  solvers, the instrument schemas, the guardrail rules stay exactly where they
  are, in Python, in this repo. A runtime backend is called for its execution
  loop and tool use; it never becomes the place solver logic lives.
- **No AGPL code is vendored.** `runtime/ollama.py` is, and stays, a direct
  Ollama HTTP adapter (this repo already has one in `providers/ollama_provider.py`;
  this plan wraps it, not replaces it). OpenMono's ideas (its hardware
  auto-detection, its `PermissionEngine`/`PathGuard`/`Capability` triad for
  tool-call gating) are welcome as design inspiration; none of its AGPL-3.0
  source is copied in. If OpenMono's own bundled-local-model convenience is
  ever wanted, it is invoked as an external, unmodified process, never folded
  into `symphysis/`.
- **One authorization decision point.** `policy/engine.py` is the only place
  a yes/no capability decision is made. `tools/authorization.py` calls into
  it; it does not re-implement its own check.

## 3. Target architecture

```
                         SYMPHYSIS
                     Governance Layer
                           |
        +------------------+------------------+
        |                  |                  |
     Passport            Policy             Audit
   (identity/)         (policy/)          (audit/)
        |                  |                  |
        +------------------+------------------+
                           |
                     Agent Runtime
                     (runtime/base.py)
                           |
          +----------------+----------------+
          |                                 |
      OpenManus                         OpenCode
       Python                          TypeScript
    (flagship backend,              (secondary backend,
     survey elicitation,             coding-heavy tasks
     ReAct + ToolCallAgent,          outside the survey
     native Ollama + cloud,          domain: FCA harness
     MCP, browser, sandbox)          work, CreatorFlow's
          |                          future script agent)
          +----------------+----------------+
                           |
                        Event Bus
                     (audit/events.py)
                           |
                     Symphysis Log
              (existing storage.py contract:
               conversation.jsonl, thoughts.md,
               card.json, did.json, result.json,
               now plus spawn_declaration.json
               and lineage.json)
```

## 4. Module layout

```
src/symphysis/
|
+-- identity/
|   +-- did.py            # = today's did_key.py, moved, unchanged
|   +-- passport.py       # = AgentCard's identity-relevant fields, extracted
|   +-- credentials.py    # = issue_credential/verify_credential, split out
|
+-- policy/
|   +-- engine.py         # the ONE authorization decision point (new)
|   +-- capability.py     # capability vocabulary + attenuation (new)
|   +-- authorization.py  # today's permissions.py checks, reframed as calls into engine.py
|
+-- agent.py              # unchanged top-level module (the existing Agent class);
|                          # NOT nested under a package, since a package and a
|                          # module cannot share the name `agent` as siblings.
|                          # RAG/websearch methods move to tools/ in Phase 2
|                          # (task 15), same as originally planned.
|
+-- spawning/              # (originally sketched as `agent/` in an earlier
|   |                      # draft of this doc; renamed during Phase 1
|   |                      # implementation to avoid the collision above)
|   +-- spawn.py          # NEW: mint child DID, issue credential, attenuate capabilities
|   +-- lineage.py        # NEW: parent_did -> [child_did, ...] tree, written to audit
|   +-- delegation.py     # NEW: what a parent is allowed to grant, vs. merely possess (not yet built)
|
+-- runtime/
|   +-- base.py           # RuntimeBackend protocol: spawn(), stream_events(), stop()
|   +-- openmanus.py      # flagship backend adapter: to_llm_settings() (pure) +
|   |                     # OpenManusBackend (launches the driver below as a subprocess
|   |                     # under vendor/openmanus/.venv, an isolated interpreter)
|   +-- _openmanus_driver.py  # runs ONLY under vendor/openmanus/.venv; the sole place
|   |                     # that imports OpenManus's own `app.*` package; emits NDJSON
|   +-- opencode.py       # secondary backend adapter (subprocess/API, TypeScript)
|   +-- ollama.py         # direct Ollama adapter (wraps existing providers/ollama_provider.py)
|
+-- tools/
|   +-- registry.py       # NEW: pluggable tool registration (RagRetrieval, CitationVerify, InstrumentSubmit, web_search)
|   +-- proxy.py          # NEW: the actual call-through a runtime backend uses to reach a registered tool
|   +-- authorization.py  # calls policy/engine.py; no independent check
|
+-- audit/
|   +-- events.py         # NEW: typed event shapes (spawn_declared, tool_called, level_completed, escalated, ...)
|   +-- logger.py         # = today's storage.py's write_* methods, generalized
|   +-- sinks.py          # NEW: pluggable sinks (filesystem, matching CreatorFlow's DB-backed trace.py shape)
|
+-- sandbox/
    +-- docker.py         # gates OpenManus's python_execute/bash tools, only for roles policy grants it
    +-- limits.py
    +-- filesystem.py
```

Everything not listed above (`instruments/`, `solvers/`, `role_packs/`,
`rag/`, `qa_checks.py`, `survey_checks.py`, `integrity.py`, `preflight.py`,
`orchestrator.py`, `cli.py`) is untouched by this plan. This is a governance
and execution-substrate change, not a rewrite of the survey domain logic.

## 5. Agent-spawn declaration: the exact contract

Every spawn, before the agent does anything else, writes
`agents/<agent-id>/spawn_declaration.json`:

```json
{
  "agent_id": "bim-coordinator-review",
  "did": "did:key:z6Mk...",
  "parent_did": "did:key:z6Mk..." ,
  "spawned_by": "orchestrator | agent:<parent_agent_id>",
  "role": "bim-coordinator",
  "capabilities_requested": ["rag_retrieval", "web_search"],
  "capabilities_granted": ["rag_retrieval", "web_search"],
  "model": {"provider": "ollama", "name": "qwen2.5:14b", "temperature": 0.7},
  "runtime_backend": "openmanus",
  "declared_at": "2026-09-01T10:00:00Z",
  "survey_id": "bsi-hawc-bwm"
}
```

`capabilities_granted` is always `intersection(parent's own granted set,
capabilities_requested)`; when `parent_did` is `null` (a human- or
orchestrator-initiated root spawn) the ceiling is whatever the survey's own
top-level permissions allow, exactly as `PermissionsSpec` already governs
today. This file is the first entry in that agent's trail, the same way the
QA precheck is today; `lineage.py` additionally maintains one
`lineage.json` per survey recording the full parent-to-child tree, so a
reviewer can reconstruct not just one agent's reasoning but who spawned whom
and with what authority, across an entire run.

## 6. Setup tasks

### Phase 0: extraction, no behavior change

1. Move `did_key.py` -> `identity/did.py`, split `issue_credential`/
   `verify_credential` into `identity/credentials.py`. Update imports.
   Existing tests must pass unmodified.
2. Split `AgentCard`'s identity-relevant construction into
   `identity/passport.py`; `agent_card.py` keeps model/rag/sampling/
   guardrails/environment as today.
3. Move `permissions.py`'s two checks into `policy/authorization.py`, calling
   a new (initially trivial, same-behavior) `policy/engine.py`.
4. Move `storage.py`'s `write_*` methods into `audit/logger.py`, keep the
   exact same on-disk file contract (`conversation.jsonl`, `thoughts.md`,
   etc.). No new files yet.
5. Full test suite green before Phase 1 starts. This phase is a pure
   refactor; if anything behaves differently, that is a bug in the refactor,
   not an intended change.

### Phase 1: capability model + spawn declaration

6. `policy/capability.py`: define the initial capability vocabulary
   (`rag_retrieval`, `web_search`, `knowledge_repo`, `code_execution`,
   `filesystem_write`, `spawn_child`). Start minimal; extend as real needs
   appear, do not pre-build capabilities nothing uses yet.
7. `policy/engine.py::attenuate(parent_capabilities, requested) -> granted`:
   set intersection, logged.
8. `spawning/spawn.py::declare_root(...)` / `mint_child(...)` / `declare_child(...)`:
   mints the child DID (reusing
   `identity/did.py::AgentIdentity.generate_deterministic/random`
   unchanged), calls `policy/capability.py::attenuate` (implemented as set
   intersection against the parent's own granted capabilities), writes
   `spawn_declaration.json` via `audit/logger.py` before returning.
9. `spawning/lineage.py`: append to `lineage.json` on every declared spawn.
10. Wire today's single-panel spawn path (`orchestrator.py`'s per-survey
    agent construction) through `agent/spawn.py` with `parent_did=None` for
    every agent (today's flat panel becomes "every agent is a root spawn").
    This makes Phase 1 land with zero change in observed behavior for
    existing surveys, while the declaration/lineage plumbing is now real and
    tested.

### Phase 2: OpenManus runtime backend

11. `runtime/base.py`: define the `RuntimeBackend` protocol
    (`spawn(task_spec, tools, model) -> RunHandle`,
    `stream_events(run_handle) -> Iterator[Event]`, `stop(run_handle)`).
12. `runtime/ollama.py`: thin adapter wrapping the existing
    `providers/ollama_provider.py`, satisfying the protocol, so the
    single-completion path (today's actual behavior) is available as the
    trivial/default backend. This is what most survey runs keep using;
    OpenManus is opt-in per agent or per survey until it is proven out.
13. `runtime/openmanus.py`: `to_llm_settings()` translates `AgentCard.model`
    into OpenManus's `LLMSettings` dict shape (confirmed: OpenManus already
    supports multiple named LLM configs, no change needed inside OpenManus
    itself for this mapping); `OpenManusBackend` drives the run.
    **Implementation note (landed during Phase 2 execution, differs from
    this task's original in-process sketch):** OpenManus's requirements.txt
    pins ~30 packages, several version-conflicting with this repo's own
    pymc/pytensor-based Bayesian solver stack, so `OpenManusBackend` does
    not import `app.*` in-process. It launches `_openmanus_driver.py` as a
    subprocess under a fully isolated interpreter at
    `vendor/openmanus/.venv` (built via `uv venv --python 3.12` +
    `uv pip install -r requirements.txt`, never the main env), and streams
    its NDJSON stdout back as `Event`s. `to_llm_settings()` itself stays a
    pure function with zero OpenManus import, so it is unit-tested without
    the isolated venv existing at all; the real subprocess path is exercised
    by a skip-if-venv-missing smoke test.
14. `_openmanus_driver.py` (co-located with `runtime/openmanus.py`, executed
    only by the isolated interpreter, never imported by Symphysis's own
    process): defines `SurveyElicitationAgent(ToolCallAgent)`, following the
    same pattern as OpenManus's own `SWEAgent`/`DataAnalysis`, with a system
    prompt specialized for BWM/AHP expert-elicitation rather than coding
    tasks, and runs its ReAct `step()` loop, emitting one JSON event per
    step to stdout.
15. `tools/registry.py` + `tools/proxy.py`: register `RagRetrieval` (wraps
    `rag/retriever.py` unchanged), `CitationVerify` (wraps
    `qa_checks.verify_sources_used` unchanged), and `web_search` (existing
    tool) into OpenManus's `ToolCollection` via the adapter, so
    `SurveyElicitationAgent` gets a real multi-turn tool loop instead of the
    current one-shot fixed-query retrieval in `agent.py`'s
    `_rag_chunks`/`_web_search_chunks`.
16. Every tool call goes through `tools/authorization.py`, which checks the
    calling agent's `capabilities_granted` from its own
    `spawn_declaration.json` before the call reaches `tools/proxy.py`.

### Phase 3: per-level instrument decomposition

17. `tools/registry.py`: add `InstrumentSubmit`, wrapping the already-fixed
    per-level `level_errors` isolation in `instruments/hierarchical_bwm.py`
    (this fix already shipped, see `diagnostics.md`'s "Reject-and-repair
    still produced accepted_count: 0" entry), now called in-loop rather than
    only at the end of a whole-response parse.
18. New `FlowType.SURVEY_PANEL` registered in OpenManus's `FlowFactory`,
    backed by `SurveyPanelFlow(BaseFlow)`: one plan step per instrument
    level, gated on `InstrumentSubmit` accepting that level before the next
    step runs. This directly targets the diagnostics.md failure mode ("one
    new error discovered per attempt, budget exhausted before convergence")
    by scoping retries to one level instead of the whole nested structure.
19. `SurveyPanelFlow`'s plan-authoring step also covers agent
    proposal/reuse, wrapping the existing `agent_proposer.py` logic
    unchanged, not rewritten.

### Phase 4: model-tiering

20. `policy/engine.py`: add an escalation rule, e.g. "a level with more than
    N criteria escalates to a configured cloud-tier model unless overridden
    per-agent-card." Default `N` and the escalation target model are a
    per-survey setting, defaulting to "no escalation" (stays local-first)
    until explicitly turned on.
21. Every escalation decision is written to `audit/events.py` as its own
    event type (`model_escalated`, with the reason and the level it applied
    to), so the trail answers "why did this level run on a cloud model"
    exactly as transparently as everything else.
22. No change required inside OpenManus itself: `runtime/openmanus.py`'s
    existing `AgentCard.model -> LLMSettings` mapping (task 13) already
    handles routing to whichever provider/model the policy engine selects.

### Phase 5: coding-capable roles (deferred until actually needed)

23. `sandbox/docker.py`, `limits.py`, `filesystem.py`: gate OpenManus's
    `python_execute`/`bash`/`str_replace_editor` tools behind
    `policy/capability.py`'s `code_execution`/`filesystem_write`
    capabilities, granted to no role by default. This phase exists for
    reuse of this control plane beyond pure survey elicitation (the FCA
    ablation harness, CreatorFlow's future script-generation agent), not
    for Symphysis's own BWM/AHP flow, and should not be built until one of
    those consumers actually needs it.
24. `runtime/opencode.py`: adapter following the same `RuntimeBackend`
    protocol as `runtime/openmanus.py`, invoked as an external process/API
    (TypeScript, never embedded in-process). Registered but not used by any
    Symphysis survey flow; available to other consumers of this control
    plane.

### Phase 6: UI

25. `TraceViewer.jsx`: add a "Lineage" tab rendering `lineage.json` as a
    tree (agent_id, did, parent, capabilities_granted), alongside the
    existing Reasoning/Prompt/Conversation-log tabs. This is additive to
    the existing component, not a rewrite.
26. Surface `model_escalated` events (task 21) in the existing Conversation
    log tab's `KIND_LABEL` map, the same pattern already used for
    `qa_precheck`/`tool_call`/`fabricated_source_citation`.

## 7. What this plan deliberately does not do

- It does not port any solver, instrument, or guardrail logic out of Python.
- It does not copy or modify OpenManus's or OpenCode's source into this
  repo's own tree; both are pinned dependencies/external processes behind
  `runtime/`. (OpenManus specifically is present as a pinned git submodule
  at `vendor/openmanus/` — a reference to the upstream repo at a fixed
  commit, not a fork or a copy — because `runtime/openmanus.py`'s subprocess
  needs its source on disk to run; nothing under `vendor/openmanus/` is ever
  hand-edited.)
- It does not change the default local-first behavior of an existing survey
  run; Phases 0-1 are designed to land with zero observable behavior change,
  and cloud escalation (Phase 4) defaults off.
- It does not build sandboxing or coding-tool exposure (Phase 5) speculatively;
  that phase is gated on an actual downstream need.
