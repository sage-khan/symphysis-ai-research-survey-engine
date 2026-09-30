# Enhancement Opportunities: symphysis-ai-research-survey-engine

**What it actually is** (corrected 2026-08-25 from an initial guess that mischaracterized it
as primarily a literature-search tool): an AI **expert-elicitation survey** engine — runs
Best-Worst Method, AHP, Delphi, and multi-level hierarchical elicitation instruments against
a panel of AI agents (each with a real `did:key` identity, declared and enforced
permissions/guardrails, and an optional per-agent RAG corpus), standing in for or alongside
a human expert panel, fully local via Ollama. It is the engine behind TrustRouter's own
AHP-weighted dimension-calibration work.

**Last updated:** 2026-09-21
**Maintainer:** Claude (on behalf of Danyal Khan)
**Per `.claude/rules/external-repo-review-standards.md`:** this is a living, single-topic
file for this one target project. New findings from future review batches are appended
here, not written into a new combined or dated-batch document elsewhere. See
`enhancement-opportunities-veritas-cogtwins-core-architecture-aug2026.md` and the other four
`enhancement-opportunities-<target-project>-aug2026.md` files in this folder for the other
topics this project's repo-review campaign has covered.

---

## Opportunities identified (2026-08-25 pass, 13 source reviews)

Scope note: this pass read 13 reviews written earlier in the same session
(`product-review-{comet,skillspector,ai-infra-guard,browser-use,openworker,old-coder,
ai-memory,neocarta,graft,contextgem,latrace-ai,exxperts,gliner25-fastino}-aug2026.md`) plus a
keyword-targeted scan of the pre-existing ~200-file review corpus (AHP/BWM/Delphi/elicitation
terms); no pre-existing-corpus file had a genuine, on-topic hit for symphysis's actual domain
at that time.

| Opportunity | Source review | What to do concretely | Priority |
|---|---|---|---|
| Multi-backend agent harness abstraction | `product-review-comet-aug2026.md` | Comet's `Harness` trait gives one typed interface over 7 heterogeneous coding-agent CLI backends (steering, interrupt, structured input-request) plus a command-ledger dedupe mechanism. Symphysis already spawns agents from portable Agent Cards across multiple model backends; review whether its own backend-dispatch layer would benefit from the same single-trait-over-heterogeneous-backends shape, particularly the dedupe-ledger idea for avoiding duplicate elicitation runs against the same agent+prompt+seed. | MEDIUM |
| RAG-corpus source expansion via structured browser automation | `product-review-browser-use-aug2026.md` | If any Symphysis Agent Card's RAG corpus needs content from login-gated or interaction-heavy sources (e.g. a paywalled standard, a portal requiring multi-step navigation) that its current retrieval approach cannot reach, browser-use's schema-driven structured-extraction actions (not just page-scraping) are a mature, MIT-licensed, well-adopted (110K+ stars) option rather than building a bespoke Selenium/Playwright flow from scratch. | LOW (only relevant if such a corpus source is ever actually needed) |
| Skill-package/agent-definition security scanning before install | `product-review-skillspector-aug2026.md` | Since Symphysis's Agent Cards are portable JSON files meant to be shared and rerun by others, SkillSpector's static+LLM scanner (69 vulnerability patterns across 17 categories) for AI-agent skill/tool definitions is a directly relevant pre-install check to run against third-party-authored Agent Cards before trusting them in a panel — a genuine "test something in experiment setup" fit, not just an inspiration. | MEDIUM |
| Auditable single-producer inspection ledger | `product-review-skillspector-aug2026.md` | SkillSpector's `inspection_ledger.py` pattern (a mathematically enforced single-producer invariant proving exactly what was scanned/skipped/failed) is directly transferable to Symphysis's own claim that "every response is schema-validated, denylist-scanned, sampled repeatedly, and checked against a QA precheck" — currently asserted in prose; this pattern would make it a machine-checkable, auditable ledger instead. | MEDIUM |

---

## Opportunities identified (2026-08-27 pass, 19 source reviews)

Scope note: all 19 reviews from this pass already contain a dedicated "Applicability to
Other User Projects" section that reads symphysis's own README directly; the items below are
the HIGH-priority or otherwise synthesis-worthy ones, not a duplicate of every review's full
per-repo paragraph (read the cited review's own section for full detail).

The single most-repeated finding across this batch is that Symphysis's own QA precheck (an
agent restates its configuration, checked against ground truth) is a **same-context
self-check**, structurally weaker than an independent, fresh-context verifier:

- `product-review-openengine-zeroshot-aug2026.md` §6 names this most sharply: restructure
  the QA precheck so the checking agent runs as a genuinely separate invocation with no
  visibility into the responding agent's reasoning trace, matching zeroshot's independence
  guarantee (a genuinely separate verifier agent that must reproduce a reported result
  rather than merely accept the executor's claim about it).
- `product-review-agentmercury-aug2026.md` §6 makes the same point via a different
  mechanism: Symphysis already separates a visible role description from an enforced
  permission gate (`permissions.py`) and QA precheck, structurally the same `R_vis`/`R_hid`
  pattern AgentMercury names explicitly; adopting AgentMercury's terminology would make an
  already-implemented idea easier to explain and audit, though Symphysis already does more
  verification (repeated sampling, denylist scanning, fabricated-citation detection) than
  AgentMercury's own grading step.
- `product-review-deepseek-harness-aug2026.md` §6 adds a complementary, narrower idea:
  reframe Symphysis's `providers.get_provider` and permission checks as an explicit
  capability seam (a Service Definition for "LLM provider access," separate Provider
  implementations per backend, the orchestrator as Consumer), and notes deepseek-harness's
  MCP client bridge as a ready template if Symphysis's agents should ever call a real
  external MCP tool server.

`product-review-ai-evals-for-everyone-course-aug2026.md` §6 adds the complementary
discipline: build a small, curated reference dataset of known-answer BWM/AHP/Delphi
weighting scenarios to regression-test a new agent-panel run or a newly added model against,
before trusting it for a real survey — Symphysis is flagged as **the repo in this entire
five-target-repo family with the most eval-adjacent practice already in place**, so this is
a genuine extension of existing discipline, not a from-scratch build.

`product-review-latticedb-aug2026.md` §6 adds a concrete, low-risk storage-model evaluation
candidate: model the agent panel, Agent Cards, per-agent raw completions, and RAG corpora as
one embedded property graph per survey run (`Agent -[:RESPONDED_TO]-> Instrument`, `Agent
-[:CITES]-> CorpusChunk`), with native vector and full-text search, all inside the one file
Symphysis already writes per survey — no new server dependency, matching Symphysis's own
local-first design goal exactly.

`product-review-bastani-atomic-aug2026.md` §6 suggests Atomic's DAG workflow pattern (typed
inputs/outputs, a bounded evidence-gated repair loop) as an internal execution model for
multi-round Delphi elicitation: a "round" stage with a typed output schema per agent, a
synthesis/evaluation stage checking convergence, and a bounded number of further rounds
rather than looping indefinitely — independent of ever depending on Atomic itself.

`product-review-llmrouter-aug2026.md` §6 flags a narrower, future-facing fit: the
cost-aware Pareto pattern (`alpha*performance - beta*cost`) for a future mode where Symphysis
runs a large panel cheaply by letting a subset of agents be served by whichever model meets
a quality floor at lowest cost, provided the Agent Card still records which model actually
answered, for reproducibility. Symphysis's per-agent model pinning is a deliberate,
reproducibility-critical design choice today, so this is a real but narrow future fit, not a
wholesale adoption.

`product-review-aiperf-aug2026.md` §6 flags aiperf's `--accuracy-benchmark {mmlu,aime}`
machinery as a **pre-flight model-vetting** use: before committing a given local Ollama
model to serve as a panelist, running it once through aiperf's accuracy benchmarks gives an
independently-reproducible capability signal, distinct from Symphysis's own QA-precheck
(which verifies self-report honesty, not general reasoning competence).

`product-review-unforgettable-aug2026.md` §6 (corrected 2026-08-28) raises a plausible,
unverified idea: if a survey run spans multiple sessions, unforgettable's `beliefs_at`/
`belief_diff` time-travel pattern could let a follow-up look ask "what did the survey-writing
agent believe about theme coverage at the start of this session versus now, and what
changed" — flagged as a suggestion, not confirmed against Symphysis's actual source.

---

## Opportunities identified (2026-09-06 pass, 26 source reviews)

Scope note: this pass covers the 26 reviews written in the 6-9 September 2026 external-repo
batch (`product-review-{unstract,ai-avatar-system,gridex,generic-knowledge-extraction-tool,
dynamic-schema-generation,gaik-toolkit,colibri,knowledge-graph-rahulnyk,agentsight,dagster,
openwhispr,gliner,openrath,lakehouse-industry-data-models,orionbelt-ontology-builder,
wemm-embedding,rag-power-bi-docs,arex-skill,mastyf-ai,open-tts-eval,scale-agentex,
vllm-agentic-api,academic-research-skills,okf-agent-memory,hermes-okf}-sep2026.md` plus
`liner-api-sep2026.md`), each read for its own dedicated "Cross-Project Relevance" section
rather than re-derived from a blanket keyword match.

| Opportunity | Source review | What to do concretely | Priority |
|---|---|---|---|
| Durable multi-agent runtime substrate | `product-review-openrath-sep2026.md` §9 | OpenRath (arXiv:2606.19409) is a session-centered runtime for multi-agent, multi-session LLM systems with checkpoints, worker leases, and an effect ledger, the strongest fit in this batch for Symphysis's own agent-panel/memory concerns. Worth a closer read of OpenRath's `Session`/`Sandbox`/`Memory` abstractions if Symphysis's orchestration layer needs durable state across a long-running survey. | MEDIUM |
| Agent Card metadata-and-boundary-documentation pattern | `product-review-academic-research-skills-sep2026.md` §9 | Academic Research Skills' per-skill metadata (`data_access_level`, `task_type`, `related_skills`) and its explicit rejected-mechanisms documentation pattern in `POSITIONING.md` is a design idea worth imitating (not importing, license reasons) for how Symphysis documents and bounds what its own AI panel agents are and are not permitted to do, extending the existing Agent Card convention. | LOW |
| Manifest-driven agent scaffolding, durable-execution reference tier | `product-review-scale-agentex-sep2026.md` §9 | Scale AI's Agentex independently arrived at the same "one portable declarative file fully specifies an agent" idea as Symphysis's Agent Card, but as a runtime/deployment descriptor rather than a persona descriptor. Its async-Temporal durability tier is a directly relevant reference if Symphysis's orchestration is ever extended toward durable, long-running multi-step survey rounds. | LOW (future-facing) |
| LLM-as-judge panel calibrated against human labels | `product-review-gaik-toolkit-sep2026.md` §9 | GAIK's `LLMJudgePanel` (multi-provider LLM-as-judge, pairwise comparison, calibrated against human labels, `validators/llm_judge/`) is a concrete alternative or complement to Symphysis's own same-context QA-precheck mechanism, already flagged in the 2026-08-27 pass as structurally weaker than an independent verifier. | MEDIUM |
| Existing TF-IDF-fallback RAG design reconfirmed as the better pattern | `product-review-rag-power-bi-docs-sep2026.md` §9 | A small comparison-only finding, not a borrow: this review confirms Symphysis's own `rag/retriever.py` (sentence-transformer cosine similarity with a dependency-free TF-IDF fallback, multi-format corpus) is architecturally more resilient than a hard OpenAI-only embedding dependency. Worth citing internally as validation that the existing design choice is sound, not a change to make. | INFO ONLY |
| Non-LLM zero-shot entity-extraction baseline | `product-review-gliner-sep2026.md` §9 | GLiNER (arXiv:2311.08526) is flagged as a directly relevant non-LLM baseline candidate if Symphysis's literature-review pipeline ever needs a cheap, CPU-capable entity/concept extraction step to benchmark against its current LLM-only approach. | LOW (only relevant if such a benchmark is undertaken) |
| Cross-session agent long-term memory, open question | `product-review-okf-agent-memory-sep2026.md` §9 | Symphysis's `storage`/`agent.py` already persists per-agent settings across sessions, and this review flags Symphysis as having the clearest genuine use case among the five sibling repos for a git-diffable, markdown-plus-YAML memory format (OKF), but this was NOT confirmed by reading `storage.py`/`agent.py` directly (out of scope for that review's "briefly check" instruction). This remains an open question for a future, more targeted look, not a confirmed finding. | LOW (needs its own targeted check before acting) |

Reconfirmed negative/no-fit findings from this pass, recorded so a future batch does not
re-investigate the same non-fit: `product-review-lakehouse-industry-data-models-sep2026.md`
§9 ("no direct relevance"), `product-review-orionbelt-ontology-builder-sep2026.md` §9 ("no
meaningful connection"), `product-review-dagster-sep2026.md` §9 (Symphysis's own bespoke
`spawning/pipeline.py` orchestrator is already correctly scoped to its actual unit of work,
agent identities with capability attenuation, not data assets), `product-review-hermes-okf-sep2026.md`
§10 ("no direct connection... not worth forcing further"), `product-review-knowledge-graph-rahulnyk-sep2026.md`
(speculative literature-concept-map fit only, not a current need), `product-review-vllm-agentic-api-sep2026.md`,
`product-review-arex-skill-sep2026.md` (a narrow parallel between AREX's procedural-skill
router and Symphysis's own Agent Library router was noted, but the two route fundamentally
different reusable-unit types, agent personas versus procedural documentation, so no action
item follows beyond noting the architectural similarity exists).

`product-review-stale-icedreamc-aug2026.md` §6 flags STALE's Premise Resistance dimension:
if Symphysis's AI panelists ever accumulate persistent, evolving positions across survey
rounds, a panelist queried with a question presupposing an earlier, now-superseded position
should resist that false premise rather than silently answering as if the old position still
held — a genuine, checkable design requirement if cross-survey memory is ever added.

---

## Cross-cutting notes relevant to symphysis

- **Agent-skill/tool-definition security scanning before trust** applies to symphysis (scan
  third-party Agent Cards before running them in a panel) and separately to
  `agenticai-polyglot-dataops-security` (scan VERITAS's own MCP layer) — see that project's
  own enhancement-opportunities file. Running the same two scanners (SkillSpector,
  AI-Infra-Guard) against both surfaces, rather than picking one tool per repo, would let the
  two repos share a common scanning dependency and cross-validate each other's findings.
- **browser-use as a shared structured-web-extraction dependency** is relevant, at
  different priority levels, to symphysis (RAG-corpus sourcing) and creator-flow
  (trend/competitive research, see that project's own file) — worth evaluating once, as a
  shared utility, rather than two separate integration decisions if both needs materialize.
- **"Propose, then require human approval before committing an autonomous
  knowledge-evolution step"** (exxperts' Checkpoint->Learn->Review Memory shape) applies here
  too, for Symphysis's own agent-position memory if cross-survey memory is ever built (see
  `product-review-unforgettable-aug2026.md`'s note above) — the same governance pattern
  recommended for VERITAS/CogTwins' ontology GROW step and for CreatorFlow's brand-voice
  profile (see their own files).
- **"Independent, context-isolated re-verification beats same-context self-check"** is the
  dominant theme for this repo specifically (see the top of this file) and is the same
  principle recommended for CogTwins' entity-extraction step and TrustRouter's Constraint
  Gates (see `enhancement-opportunities-veritas-cogtwins-core-architecture-aug2026.md`).

---

## 2026-08-30 Batch: Coding-agent-harness cluster + ontology/orchestration repos

Findings from a ~20-repo batch covering the Claude-Code-harness cluster (leaked-source
mirrors, PikoClaw, opencode, deepseek-harness, claw-code, Agent Orchestrator, JIT-Agent) plus
Ontology Atlas, NVIDIA Model Optimizer, adaptann, Hyper-Extract, and freephdlabor. Full
per-tool detail in each tool's own `product-review-*-aug2026.md`; the cross-cluster synthesis
is `product-review-coding-agent-harness-comparison-aug2026.md`.

- **Symphysis's `did:key` Agent Card model is already stronger than anything found natively
  in the coding-agent harnesses reviewed this batch** (opencode, PikoClaw, deepseek-harness,
  claw-code, Agent Orchestrator) — none has a comparable cryptographically-scoped,
  capability-checked agent identity. Two follow-up reads are worth doing before assuming
  Symphysis has nothing to learn here: opencode's dedicated `identity/` package and
  deepseek-harness's `identity` package family were both noted but not read in depth this
  session (see `product-review-coding-agent-harness-comparison-aug2026.md` §5).
- **JIT-Agent's M/P/A/F (Memory/Planning/Action/Capability) harness factorization** is a
  candidate design vocabulary for formalizing how each Symphysis agent's internal loop is
  composed, and its **seed-bank-of-baseline-harnesses** pattern (a fixed library of named,
  documented baseline designs fed to a generator as few-shot reference material) is directly
  reusable if Symphysis ever needs to compare fixed vs. task-adapted agent structures for
  different survey-domain tasks (`product-review-jit-agent-harness-aug2026.md` §7).
- **deepseek-harness's capability-seam vocabulary** (Service Definition / Service Provider /
  Consumer) is a reusable structuring pattern for Symphysis's `providers.get_provider` and
  permission-check code: reframing "LLM provider access" as an explicit seam (one interface,
  swappable providers, the orchestrator as consumer) makes the permission-enforcement
  boundary a named, reviewable interface rather than an ad hoc function call scattered
  through `orchestrator.py`. Its MCP client bridge (`mcp__<serverName>__<rawName>` tool
  namespacing) is also a ready template if Symphysis's agents should call out to a real
  external MCP tool server (a shared literature-search or citation-verification server)
  rather than only the built-in `web_search`/RAG tools (`product-review-deepseek-harness-aug2026.md`
  §6, carried forward from the 2026-08-27 review, restated here as still directly relevant to
  this batch's harness-comparison focus).
- **If Symphysis's agent panel is ever run at scale across many agents/conditions in
  parallel**, Agent Orchestrator's Kanban-style live-status-derivation pattern (status
  computed at read time from durable facts, never stored) is a directly borrowable dashboard
  pattern independent of adopting AO itself (`product-review-untrivial-agent-orchestrator-aug2026.md`
  §4).
- **opencode and PikoClaw are worth trialing as the actual coding-agent harnesses** if
  Symphysis or a related experiment ever needs a general-purpose, provider-agnostic
  coding-agent loop rather than its own purpose-built survey-elicitation engine — not a
  replacement for Symphysis's core engine, but a candidate harness for any adjacent
  "run an agent against a real coding task across multiple LLMs" need. See
  `product-review-coding-agent-harness-comparison-aug2026.md` §2 for the full comparison and
  recommendation.

---

## 2026-08-31: Extract `did_key.py`/`agent_card.py`/`storage.py` Into a Standalone Package

The open follow-up from the 2026-08-30 batch above (whether opencode's or deepseek-harness's
`identity` packages already provide something Symphysis would need to import) is now closed:
opencode's `identity/` package turned out to be brand/logo image assets, and deepseek-harness's
is a bare anonymous-telemetry UUID with no keypair or credential (both confirmed by direct
source read this session; `product-review-coding-agent-harness-comparison-aug2026.md` §5,
updated 2026-08-31). Symphysis's `did_key.py`/`agent_card.py`/`storage.py` remain, confirmed,
the most sophisticated agent-identity-plus-trace implementation in this entire multi-repo
review campaign, not merely an assumption carried forward from the earlier batch.

**Concrete next step, grounded in what already exists rather than a new design**:
`creator-flow/shared/agent_card/` is a working, already-shipped proof that this exact code
generalizes past Symphysis's own survey-elicitation domain: its `card.py` and `did_key.py`
docstrings state outright they were ported/adapted from Symphysis's own files, and its
`trace.py` is wired into CreatorFlow's real database (`agent_runs.trace_ref`) as a shipped
Phase 1 feature (see `enhancement-opportunities-creator-flow-aug2026.md`'s own 2026-08-31
section for the full detail, including a real capability gap the hand-port introduced:
CreatorFlow's copy dropped Symphysis's `issue_credential`/`verify_credential` Verifiable-
Credential methods). Two repos independently maintaining hand-synced copies of the same three
files is the predictable path to silent drift; the next concrete step for Symphysis's own
codebase is to extract these three modules into one standalone, framework-free Python package
(versioned, installable via a local path or internal index) that both Symphysis and CreatorFlow
depend on rather than fork. `storage.py`'s survey-specific folder layout
(`surveys/<id>/agents/<id>/...`) is the one piece that would need to become a parameterized,
host-project-supplied path convention rather than a Symphysis-specific constant, since
CreatorFlow's `trace.py` already writes to a different persistence target (its own database,
via `agent_runs.trace_ref`) rather than Symphysis's flat-file `surveys/` tree.

Once extracted, the same package becomes the direct answer to "can one of the reviewed
coding-agent harnesses be used for the whole spawning pipeline": wrap each spawn of whichever
harness a given task needs (opencode/PikoClaw for cloud multi-provider work, OpenMono for
zero-cost local sweeps, deepseek-harness for sandboxed execution, OpenManus for multi-agent
planning/flow workloads once its own review lands) in this package as the identity-minting,
hyperparameter-recording, trace-capturing layer, exactly as Symphysis's own `Agent.run` already
wraps every provider call today (`src/symphysis/agent.py`) — the harness supplies the execution
loop, the extracted package supplies the passport and the flight recorder.

## Opportunities identified (2026-09-07 pass, 5 source reviews: eLLM, heretic, labs-molt, LocalAI, secant)

| Opportunity | Source review | What to do concretely | Priority |
|---|---|---|---|
| Reranker backend for RAG retrieval quality | `product-review-localai-sep2026.md` §9 | Symphysis's `embedding_providers` adapter (`ollama_provider.py`, `openai_compatible.py`) already mirrors its LLM-provider pattern for local, zero-data-leaves-the-machine embedding via Ollama (`nomic-embed-text`), but has no reranking stage. LocalAI's `rerankers` backend (wrapping `AnswerDotAI/rerankers`) is a genuine, concrete improvement candidate for symphysis's own brand-voice/knowledge-base RAG retrieval quality: a two-stage retrieval pattern (fast retriever finds candidates, cross-encoder reorders by relevance) it does not currently have. A wholesale LLM-backend swap away from Ollama is NOT warranted, Ollama already serves symphysis's stated need for local, multi-family model support (Qwen, Gemma, Llama, Mistral, DeepSeek, Phi per the README's example survey roster). | MEDIUM |
| Speculative, unconfirmed long-horizon note: local-LLM agent backend diversity | `product-review-ellm-cpu-inference-sep2026.md` §9 | Noted only as a speculative, unconfirmed possibility, not a genuine fit: if symphysis's local-Ollama agent panels ever need long-context ingestion (e.g., a survey agent reading a very long source document) rather than short-context BWM/AHP comparison prompts, eLLM's CPU long-horizon inference claim is theoretically relevant, but its headline "faster than GPUs" claim is unsubstantiated by its own bundled paper (see the VERITAS-core-architecture file's entry) and it carries an AGPL-3.0 licensing consideration. Do not act on this without a concrete long-context workload actually appearing in symphysis first. | LOW (speculative) |
| Speculative, unconfirmed long-horizon note: RL-trained agent-proposal step | `product-review-labs-molt-agentic-rl-sep2026.md` §9 | Symphysis's `agent_proposer.py` (turns a plain-language requirement plus an LLM call into a reviewable, editable list of proposed agents) is, in principle, a policy that could eventually be trained via reward signal rather than a single zero-shot LLM call, which is conceptually what NVIDIA's Molt framework (arXiv:2607.21653) targets. This is speculative and long-horizon only: Molt requires multi-GPU CUDA-13 hardware symphysis has no evidence of needing or having, and is 10 weeks old. No action recommended today; noted for awareness only. | LOW (speculative, long-horizon) |

Checked and found no fit from this pass: `product-review-heretic-abliteration-sep2026.md`
(a defensive/red-team security tool; symphysis's threat surface, if any, is not this repo's
concern) and `product-review-secant-rope-softmax-sep2026.md` (a transformer-attention-internals
paper; symphysis consumes models purely through Ollama's inference API, never touching
attention-internals computation, so there is no layer of symphysis's stack this identity
could apply to).

## Opportunities identified (2026-09-15 pass, 17 source reviews)

Scope note: this pass covers the batch of 17 reviews dated `sep2026` written 2026-09-15
(`product-review-{hyperresearch,feynman,llm-wiki,diskwatch,pyrit-llm-red-teaming,blayers,
resilience-ledger,optimar-ontology,ontop,nvidia-osmo,cccc,spotify-portal-ai-plugins,
model-compose,owlapy,earendil-pi,ephemora-cell}-sep2026.md` plus a freshness addendum to
`product-review-semantica-jul2026.md`, which carries no symphysis-relevant content and is
not otherwise discussed below), each read for its own "Cross-Project Relevance Flag" section
and, for the higher-priority items, its full "What could be borrowed" treatment.

### BLayers vs. Symphysis's own Bayesian BWM solver: do not migrate, but three patterns are worth taking

`product-review-blayers-sep2026.md` was written specifically to answer whether BLayers (a
NumPyro/JAX Bayesian-regression composition library) is a stronger foundation than
Symphysis's own from-scratch, PyMC-based hierarchical BWM solver (`src/symphysis/solvers/
bwm_bayesian.py`, `hierarchical_bwm.py`). The review's conclusion is unambiguous and worth
restating precisely: **do not migrate.** BLayers is NumPyro/JAX-only by explicit design,
Symphysis's solver is PyMC/PyTensor, so any migration would mean rewriting the solver on a
different probabilistic-programming stack, not a drop-in swap. More importantly, BLayers'
own correctness tests are internal-consistency checks only (hand-derived reference
distributions built from the same NumPyro primitives the library itself calls), while
Symphysis's `bwm_bayesian.py` is verified line-for-line against Mohammadi and Rezaei's
published reference JAGS implementation (`github.com/Majeed7/BayesianBWM`), a genuine
external, cross-tool validation that found and fixed a real hyperprior discrepancy
(`Gamma(1, 0.01)` versus the reference's `Gamma(0.01, 0.01)`). Symphysis's validation
discipline is already the stronger one for a methodology paper whose credibility rests on
matching a published reference implementation; BLayers offers nothing to strengthen that
claim and would in fact be a regression if cited as an equivalent validation approach.

What the review does recommend, as reusable design patterns independent of ever depending
on BLayers as a package:

1. **Plate-free batched-VI ELBO guard** (`blayers/vi_infer.py`'s `Batched_Trace_ELBO`). It
   rescales the observed log-likelihood by `num_obs / batch_size` for minibatched
   variational inference without requiring `numpyro.plate`, and, critically, hard-fails with
   a `ValueError` (`_raise_if_has_plate()`) if a model trace contains a `plate` site, because
   that combination would silently double-count and produce a wrong ELBO. If Symphysis's own
   PyMC solvers ever need minibatched VI for a large panel, the concrete lesson is the
   fail-loudly-on-a-known-wrong-combination discipline, not the NumPyro code itself.
2. **Compatibility-matrix test pattern** (`tests/inference_compatibility_test.py`'s `CALLS`
   dict plus `test_all_builtin_layers_have_inference_coverage()`, which fails the suite if
   any exported layer is missing an explicit test recipe). This is directly portable to
   Symphysis's own `tests/test_hierarchical_bwm_solver.py` and `tests/test_bwm_bayesian.py`:
   a dict mapping every registered instrument/solver variant (classical BWM, Bayesian BWM,
   hierarchical BWM, and any future third method) to an explicit test recipe, with one test
   that fails the suite outright if a newly added variant ships without a recipe entered.
   This turns "every solver must have a compatibility test" from a convention someone has to
   remember into a mechanically enforced gate.
3. **Model-to-LaTeX tracer** (`blayers/latex.py`'s `model_to_latex()`, which traces a fitted
   or unfitted model once and renders its exact prior/likelihood structure as LaTeX `\sim`
   statements). Symphysis's own Bayesian hierarchical BWM model could have an equivalent
   tracer that emits its exact prior/likelihood structure directly from `bwm_bayesian.py`
   for the Symphysis paper's methods section, removing a class of hand-transcription error
   between what the fitted model actually is and what the paper claims it is, an especially
   relevant gap given this project's own mandatory citation-precision rules.

A fourth, smaller finding: BLayers' CHANGELOG discipline (documenting removed features and
default-behavior changes with an explicit migration note, not just additions) is a pattern
Symphysis's own solver modules already follow once (the `Gamma(1,0.01)` to
`Gamma(0.01,0.01)` fix is already documented in `bwm_bayesian.py`'s own docstring); BLayers
is worth citing internally as a model for keeping that habit up consistently as more fixes
accumulate, not as a new practice to adopt.

### Three multi-agent-orchestration candidates for Symphysis's own panel sessions

Three reviews in this batch each propose a different piece of infrastructure Symphysis's
own multi-agent panel orchestration could be compared against or built on. Read together,
they sit at three different levels of the stack and are not mutually exclusive:

- **`product-review-cccc-sep2026.md`: closest in spirit.** CCCC coordinates independent AI
  coding-agent CLI sessions as peers in a persistent group chat, backed by a single-writer,
  append-only ledger that separates "a message was delivered," "a message was read," and "a
  message was replied to or a delegated task completed" into three distinct, never-conflated
  facts (never inferred from what is missing). This is the same shape of problem Symphysis
  already has today, coordinating a panel of independently spawned agents, and CCCC is a
  concrete, shipping reference for exactly this durable-coordination substrate. Two specific
  patterns transfer directly: the delivery/read/reply fact-separation model, worth comparing
  against however Symphysis's `spawning/pipeline.py` and `storage.py` currently record
  whether a given panel agent actually completed its elicitation turn, and the `tracked-send`
  primitive (a delegated task with a title, an outcome/acceptance criterion, and a durable
  owner), which maps cleanly onto "this agent was assigned this BWM comparison round, and
  here is whether its acceptance criterion, a schema-valid, QA-precheck-passing response, was
  met." CCCC's own versioned protocol-contract documents (`docs/standards/CCCC_*_V1.md`) are
  also a good documentation pattern if Symphysis's own Agent Card schema or panel wire format
  is ever exposed to a third party building against it.
- **`product-review-earendil-pi-sep2026.md`: a lower-level runtime Symphysis could build
  agents on top of, not a coordination-layer peer.** `pi` (`earendil-works/pi`) is a minimal,
  formally specified agent-loop-plus-harness runtime with 38 documented crash-recovery
  invariants, three interchangeable session-storage backends passing one shared conformance
  suite, and a broad, actively maintained multi-provider LLM abstraction (`pi-ai`) already
  reused wholesale by at least one other independent project. Two patterns are concretely
  reusable regardless of whether Symphysis ever depends on `pi` directly: the intent-then-
  settlement transaction pattern (commit a durable intent before an uncertain external
  effect such as a provider call, commit the complete settled outcome after, so a crash
  mid-call never leaves an agent's turn in an ambiguous state and never risks double-charging
  or double-sampling a completion), and the never-throw stream contract (a provider stream
  failure becomes a terminal message with a typed `stopReason` rather than an unhandled
  exception, and a `stopReason == "length"` truncation fails every tool call in that turn
  rather than risking execution against truncated JSON). The `AgentTool<T>` contract
  (name, schema, `execute(toolCallId, args, signal, onProgress)`) is also a clean template
  for how Symphysis's own per-agent tool surface (currently a fixed BWM/AHP solver call) could
  be typed if it ever grows beyond that single call. `pi-ai` specifically is worth flagging
  as the single most concrete, lowest-effort borrow of the three reviews in this trio: it
  already supports both Ollama-compatible local endpoints and every major commercial
  provider (Anthropic, OpenAI, Google, Bedrock, Mistral, OpenRouter) behind one typed
  interface, which is exactly the provider-mixing shape Symphysis's own `providers.
  get_provider` already has to solve by hand.
- **`product-review-nvidia-osmo-sep2026.md`: least directly applicable, but its MCP design
  is still worth a look.** OSMO is a Kubernetes-native compute-cluster workflow orchestrator
  (scheduling containerized tasks onto GPU clusters), a categorically different granularity
  from anything Symphysis needs, an agent panel round is an LLM call, not a scheduled pod,
  and OSMO's task-DAG idiom assumes full-container execution units. The one transferable
  piece is OSMO's deliberately narrow, read-only-first, RBAC-preserving MCP tool surface
  (`src/service/mcp/TOOLS.md`: phase the tool surface read-only before mutation, document
  exactly which upstream call each tool maps to, explicitly state what is never returned,
  such as credential payloads, and cap/redact long responses with a documented bound).
  Symphysis does not currently expose an MCP server; if it ever does (for a third party to
  query panel status or results without the full CLI), OSMO's phasing and redaction
  discipline is a directly citable template.

Priority ordering for this trio: cccc is the closest-fit reference architecture (HIGH) since
it solves the same coordinating-independent-agents problem Symphysis already has; `pi` is a
credible foundation for a future rebuild of Symphysis's own agent-execution layer, not an
urgent need (MEDIUM), since Symphysis's existing Agent Card/`did_key.py`/provider-dispatch
code already works; OSMO is the weakest fit (LOW), relevant only for its MCP-exposure
pattern if Symphysis ever adds a server-facing API surface.

### Feynman's PaperRank scoring design and Hyperresearch's tool-allowlist pattern

| Opportunity | Source review | What to do concretely | Priority |
|---|---|---|---|
| Evidence-and-confidence scoring wrapper for every response/dimension score | `product-review-feynman-sep2026.md` §9 | Feynman's `ScoreSignal` pattern (`src/rank/paper-rank.ts`'s `signal()` helper) attaches four fields to every one of PaperRank's six scoring dimensions: a numeric value, an `available` boolean (was there actually data to compute this, or is it a forced default), a confidence tier (high/medium/low), and a rationale string plus an evidence-triple list. Symphysis's own per-agent BWM/AHP response already carries raw completions and QA-precheck results; wrapping each parsed response (or each solved weight in the final report) in the same {value, available, confidence, rationale, evidence} shape would make a Symphysis survey result auditable at the individual-response level in a way closely matching what a reviewer of the planned OREJ paper is likely to ask for: why is this specific agent's or dimension's weight what it is, and what evidence backs the confidence attached to it. | MEDIUM |
| Anti-fabrication subagent operating contract | `product-review-feynman-sep2026.md` §9 | Feynman's bundled `verifier.md` subagent enforces an "orphan-citation, orphan-source symmetry" rule and bans writing "verified"/"confirmed"/"reproduced" without a traceable check. Symphysis's guardrails (schema validation, denylist scanning, repeated sampling, QA precheck) already cover a similar anti-fabrication space for panel responses; Feynman's specific symmetry check is a narrow, concrete addition worth comparing against Symphysis's report-generation step specifically (does the generated Markdown report's Methodology section ever assert a genuineness check ran without a corresponding logged QA-precheck record backing it). | LOW |
| Existing tool-allowlist enforcement pattern reconfirmed as directly relevant | `product-review-hyperresearch-sep2026.md` §9, §11 | Hyperresearch's patcher/polish-auditor subagents are restricted, at the Claude Code tool-allowlist level rather than by prompt instruction alone, to `[Read, Edit]`, so a "make only surgical edits" instruction cannot be silently ignored by the model. This is a concrete, already-shipping example of exactly the "enforced (not merely documented) permission and guardrail architecture" Symphysis's own paper (paper 4 in `project-details.md`) is already building toward with `permissions.py`'s data-scope and provider allowlisting; the specific new detail worth citing is that Hyperresearch enforces this at the *harness tool-access* layer (what tools a subagent process can even invoke), a different enforcement point than Symphysis's current *data-path and provider* enforcement, worth naming as a complementary layer if Symphysis's agents are ever run inside a coding-agent harness (Claude Code, `pi`, or similar) rather than called directly via a provider API. | MEDIUM |

### Smaller and negative findings from this pass

- **`product-review-model-compose-sep2026.md` §10, §12**: model-compose's interrupt/resume
  human-in-the-loop state machine (`TaskStatus.INTERRUPTED`, a `resume_workflow(...)` call
  carrying a structured answer keyed by the pending call's ID, with a concrete reference
  implementation at `tests/e2e/controller/test_agent_external_tool_interrupt.py`) is a
  directly applicable pattern if Symphysis's panel runs ever need a human approval gate
  (for example, pausing a survey run for a human sign-off on a flagged or borderline
  response before it counts toward the solved result), rather than only a QA precheck that
  runs unattended. MEDIUM priority, concrete and cheap to prototype against.
- **`product-review-ephemora-cell-sep2026.md` §9, §11**: Cell's governed dynamic-tool-loading
  pattern (ADR-006: an agent proposes a tool it wants, the host disposes, deciding whether to
  grant it) is directly applicable, but only once Symphysis's agents are given tool-calling
  or code-execution capability beyond calling a fixed BWM/AHP solver, which is not the
  current architecture. Recorded as a forward-looking design constraint to apply at that
  point, not an action item today. LOW priority, contingent on a capability Symphysis does
  not yet have.
- **`product-review-owlapy-sep2026.md` §12**: flagged as low-to-moderate relevance only.
  AGen-KG's dspy-based multi-signature agent design (a `PlanDecomposer` plus incremental
  mergers and clustering/coherence-checking signatures, all as structured dspy pipeline
  stages) is a concrete example of a structured, multi-stage LLM-pipeline pattern that could
  inform how Symphysis's own agent-orchestration code is factored, but the domains
  (ontology construction versus expert-elicitation survey response) differ enough that this
  is inspiration, not a specific borrow. LOW priority.
- **`product-review-spotify-portal-ai-plugins-sep2026.md` §10, §12**: the named/resolvable
  "mode" concept (fork-and-override with automatic precedence, prefer the caller's own copy,
  then their group's, then a public default) is worth a comparison against Symphysis's own
  Agent Card/Agent Library resolution logic, to check whether Symphysis already has an
  equivalent override-precedence rule for a user-customized Agent Card versus a shared
  library default. Not confirmed against Symphysis's actual source in that review (out of
  its own stated scope); flagged as a question for a future, more targeted look, not a
  confirmed gap. LOW priority.
- **`product-review-llm-wiki-sep2026.md` §11, §12**: no strong borrow, but worth recording
  because it independently validates an existing Symphysis design choice: the review
  explicitly flags llm_wiki's own hardcoded, uncalibrated relevance weights as a pattern
  VERITAS/Symphysis should NOT copy, since TrustRouter's AHP expert-elicitation approach
  (run via Symphysis's own BWM/AHP surveys) is already the more defensible way to weight
  multiple signals. INFO ONLY, no action item, cited here so a future pass does not
  re-investigate llm_wiki's two-step chain-of-thought ingest pattern expecting a stronger
  fit than the review actually found.
- **No fit found, reconfirmed so a future pass does not re-investigate**:
  `product-review-diskwatch-sep2026.md` §12 ("no meaningful relevance"),
  `product-review-optimar-ontology-sep2026.md` §12 ("not relevant; no expert-elicitation or
  survey-methodology content"), `product-review-ontop-sep2026.md` §12 ("not relevant"),
  `product-review-resilience-ledger-sep2026.md` §12 (a loose analogy only, "every AI-drafted
  contribution stays candidate until a human cold read" as a human-in-the-loop discipline
  comparison, not a code-adoption candidate), `product-review-pyrit-llm-red-teaming-sep2026.md`
  §12 (worth a look only if Symphysis's panel agents ever need adversarial-robustness testing
  against prompt injection from a malicious survey response, not a current fit), and the
  `product-review-semantica-jul2026.md` freshness addendum (no symphysis-relevant content).

## Opportunities identified (2026-09-21 pass, 15 source reviews)

Scope note: this pass covers 15 reviews from the mid-to-late September 2026 batch
(`product-review-{lpg-modeler,tgrep,sstorytime,memos,grounded-document-agent,omnigraph,
mnestic,paper2agent,superagent,jev-ultrafast,evoontology,helix-db}-sep2026.md`,
`product-review-microsoft-fabric-platform-sep2026.md`,
`product-review-microsoft-fabric-graph-database-sep2026.md`, and
`product-review-azure-cosmos-db-sep2026.md`), each read for its own "Enhancement
Opportunities" / "Relevance to VERITAS/CogTwins and Enhancement Opportunities" section
naming Symphysis specifically, rather than re-derived from a blanket keyword match.

### Paper2Agent: the highest-priority finding of this pass, two distinct opportunities

`product-review-paper2agent-sep2026.md` reviews a peer-reviewed (Nature, 2026) tool that
converts a research paper's own codebase into a reliability-verified, natural-language
callable MCP server. Two separate, concrete opportunities for Symphysis follow from it,
named explicitly in that review's §9:

1. **Adopt the mandatory fresh-agent implementer/verifier separation for the Agent
   Library** (`product-review-paper2agent-sep2026.md` §2.2, §4.2). Paper2Agent requires a
   distinct, freshly spawned verifier agent, one with no shared context with the agent that
   wrote the code, to independently confirm each generated tool's output against the source
   paper's own reference outputs (numerically bounded floating-point tolerance, perceptual-
   hash figure matching, bounded repair attempts, hard exclusion on repeated failure) before
   it ships. Applied to Symphysis's own Agent Library: when a new agent persona or survey-
   instrument tool is added, require a distinct verifier agent, never the same context that
   implemented the tool, to independently confirm its output against a reference calculation
   before it is added to the library's callable set. This targets, structurally rather than
   by chance, exactly the class of defect this project has already caught in Symphysis's own
   history: the HAWC-BWM Bayesian hierarchical-BWM Gamma-prior bug (`Gamma(1, 0.01)` versus
   the correct `Gamma(0.01, 0.01)`), found only because someone happened to check the solver
   against Mohammadi and Rezaei's published reference JAGS implementation
   (`github.com/Majeed7/BayesianBWM`), not because a structural verification gate caught it.
   Priority: HIGH.
2. **Package the Bayesian hierarchical BWM solver as a standalone, independently-callable
   MCP server using Paper2Agent's tri-part tools/resources/prompts structure**
   (`product-review-paper2agent-sep2026.md` §7.1, §4.1). This would let the planned Symphysis
   paper (`symphysis-ai-panel-elicitation.tex`, target OREJ, Q1 2027) ship an "agent
   availability" artifact alongside the manuscript, matching the paper's own anticipated
   Discussion point that reviewers will soon expect an agent-callable artifact on par with a
   code repository or example notebook, and giving reviewers a way to independently query and
   re-run the panel-elicitation methodology without installing Symphysis's own codebase.
   Priority: MEDIUM (concrete, but contingent on the solver and paper both reaching a stable
   state first).

### Automating the ManualProvider web-chat-UI arm

`product-review-jev-ultrafast-sep2026.md` §8 identifies its own review's single most
concrete cross-project finding here: Symphysis's `src/symphysis/providers/manual_provider.py`
docstring describes exactly the workflow jev-ultrafast's technique targets, a human copying a
prompt into a web chat UI with no API (ChatGPT, Gemini) and pasting the reply back. Its
indexed-element-snapshot, single-request "what operation, which target" decision, and
independent-outcome-verification loop is directly applicable to automating both manual steps
(typing the prompt into the chat box, reading the reply back out of the page) for every
`trustrouter-*-manual-*` survey run under `symphysis-ai-research-survey-engine/surveys/`,
removing the human-in-the-loop step while preserving the exact evidentiary property that
matters: the response genuinely came from the consumer-facing product a disclosed AI-tool
user would actually encounter, not the API. Any such build must reuse the person's own
already-authenticated local browser session (a local CDP connection, as jev-ultrafast/Browser
Harness does), never a stored-credential replay against ChatGPT's or Google's terms of
service, and is named here as a candidate for a future scoped design, not a recommendation to
build today. Priority: MEDIUM (concrete and well-specified, but not urgent, since the current
manual workflow already functions correctly, only with a human-labor cost).

### Provider-qualified model router as a minimal reference implementation

`product-review-superagent-sep2026.md` §9 flags SuperAgent's `internal/model/client.go`, a
single `Client.Complete` dispatching by provider tag across OpenAI/Anthropic/Gemini/Groq/mock
with credentials held only in process memory and never logged or persisted, as a minimal,
clean reference for exactly the kind of multi-provider dispatch Symphysis's own Agent Library
already needs when running a panel across heterogeneous model backends. The specific,
checkable action item is narrower than "adopt this pattern": compare Symphysis's own provider
credential handling in `providers.get_provider` against this never-log-or-persist discipline
to confirm it already holds, since this was not itself verified against Symphysis's source in
that review (out of its stated scope). Priority: LOW (a verification task, not a confirmed
gap).

### HelixDB as a combined graph-plus-vector memory store for past elicitation sessions

`product-review-helix-db-sep2026.md` §2, §4 flags HelixDB's positioning as a database "for
knowledge graphs and AI memory," combining graph relationships with vector similarity in one
transactional engine, as a direct match for a capability Symphysis does not currently have:
an AI panel agent's own episodic or semantic memory of past elicitation sessions, letting a
future look ask "find similar past decisions" via combined graph traversal and vector
similarity in one query, rather than wiring together two separate memory backends by hand.
The review proposes a concrete, small-scope prototype: store one AI panel's prior elicitation
run (its recorded rationale chain, weight outputs, and any embedded free-text justification)
in a local HelixDB instance and test whether its traversal-then-vector-search query shape
surfaces genuinely relevant prior sessions faster or more simply than Symphysis's current
storage. Priority: LOW (a prototype-worthy idea, not a confirmed need, since Symphysis has no
current cross-session memory requirement; related to the still-open question flagged in the
2026-09-06 pass from `product-review-okf-agent-memory-sep2026.md` about whether Symphysis
needs a cross-session memory format at all, this is a second, independent candidate mechanism
for that same open question rather than a settled answer to it).

### Smaller findings

| Opportunity | Source review | What to do concretely | Priority |
|---|---|---|---|
| N4L low-friction note syntax for elicitation-transcript authoring | `product-review-sstorytime-sep2026.md` §9.4 | N4L's design goal, letting a human or agent jot `subject (arrow) object` triples without upfront schema commitment, then tidy or retype later, is a plausible lightweight intermediate format for capturing raw AI-panel elicitation reasoning traces before they are structured into Symphysis's formal BWM/AHP judgment records. Its closure-rule mechanism (auto-deriving inverse/derived relations) maps naturally onto auto-deriving reciprocal pairwise-comparison entries. | LOW |
| Shared ontology-grounding object for panel-agent consistency | `product-review-microsoft-fabric-platform-sep2026.md` §8 | Fabric IQ's design principle of grounding every agent in one shared ontology/semantic layer before it reasons is a pattern Symphysis's AI-panel agents could adopt more explicitly: giving every panel agent the same shared domain-ontology context object before elicitation, rather than relying solely on prompt-level instructions, could improve cross-agent consistency on a shared elicitation instrument, directly relevant to the TrustRouter trust-dimension weighting survey Symphysis already runs. | LOW |

### No fit found, reconfirmed so a future pass does not re-investigate

`product-review-lpg-modeler-sep2026.md` (no symphysis mention anywhere in the review; its
enhancement sections cover only VERITAS/CogTwins core architecture and
`fca-guided-ontology-gen-llms`), `product-review-tgrep-sep2026.md` §9 ("No enhancement
opportunity was found for `symphysis-ai-research-survey-engine`... none of those projects'
actual mechanisms... have a genuine touchpoint with a trigram-indexed source-code search
tool"), `product-review-memos-sep2026.md` §10 (MemOS's `MemLifecycle` finite-state model and
`MemGovernance` permission model are directed at `project-cogtwins` and
`agenticai-polyglot-dataops-security` specifically; no symphysis section is offered),
`product-review-grounded-document-agent-sep2026.md` §8 (enhancement opportunities named only
for `text2officeprocessor` and `project-cogtwins`'s document-pipeline query layer; its
citation-grounding mechanism answers a document-QA question, not an expert-elicitation-panel
question, and the review does not force a symphysis connection), `product-review-omnigraph-sep2026.md`
§9 ("no direct relevance found... Omnigraph is an infrastructure/database product with no
document-processing, survey-elicitation, or content-creation functionality"),
`product-review-mnestic-sep2026.md` §8 ("none of mnestic's specific mechanisms... map to a
genuine, concrete need"), `product-review-evoontology-sep2026.md` (enhancement opportunities
named only for `fca-guided-ontology-gen-llms` and `project-cogtwins`; no symphysis mention
anywhere in the review), `product-review-microsoft-fabric-graph-database-sep2026.md` §10 ("No
concrete enhancement opportunity identified for `symphysis-ai-research-survey-engine`... this
is a cloud-platform storage-engine product with no... expert-elicitation... surface relevant
to those projects' actual mechanisms"), and `product-review-azure-cosmos-db-sep2026.md` §8
("No concrete, honest borrow was identified for... `symphysis-ai-research-survey-engine`...
Cosmos DB is a cloud database service with no... expert-elicitation... surface relevant to
those projects' actual mechanisms").

---

## Opportunities identified (2026-09-21 pass 2, 11 source reviews)

Scope note: this second pass on the same date covers the 11 reviews from a separate,
later-arriving batch (`product-review-{operational-ontology,claude-reverse-proxy,scienceide,
bendlang-bend,agentpick,dex,dream-rsi}-sep2026.md`, `blog-review-{loftwah,pedramamini,
pjburnhill-typesafe-jev}-gist-sep2026.md`). This is the **richest pass-2 batch found across all
six sibling-project files**: every one of the 11 reviews named a fit here, and
`product-review-claude-reverse-proxy-sep2026.md` independently calls Symphysis "the strongest
match of the five" named sibling projects.

| Opportunity | Source review | What to do concretely | Priority |
|---|---|---|---|
| Reverse proxy collapsing per-provider Agent Card call paths onto one Anthropic-SDK path | `product-review-claude-reverse-proxy-sep2026.md` §9 | Symphysis already runs a 6-Ollama-model-plus-Claude tier panel with each provider getting its own direct call path (confirmed: `surveys/trustrouter-hawc-bwm-slm-run1-2026-09-01-L2/agents/blockchain-engineer-base-ollama.json` sets `"model": {"provider": "ollama", ...}` with `"runtime_backend": "direct_completion"`). A reverse proxy making every Ollama-hosted or cloud-hosted model answer to a single Anthropic-shaped client would let the orchestrator drive every panel member through one call path (the `anthropic` SDK) regardless of which provider an Agent Card names, simplifying current per-provider branching without changing the panel methodology itself. Worth a genuine look during the next orchestrator refactor; not urgent, and given the tool's three-day age, pin an exact commit and keep it local-only if adopted. | MEDIUM |
| Check/warrant discipline for grading AI-panel response quality | `product-review-scienceide-sep2026.md` §10.1 | ScienceIDE pairs every graded check with a plain-language warrant (what the observable is, which bias the bound distinguishes, why a valid answer can satisfy it). Apply this documentation discipline to Symphysis's own consistency/validity gates on AI-panel BWM/AHP judgments (analogous to a BWM consistency-ratio gate), making explicit why a given consistency threshold is the right one rather than an arbitrary cutoff. | MEDIUM |
| Reproducible-episode-interface pattern as external validation of the Agent Card design | `product-review-scienceide-sep2026.md` §10.1 | ScienceIDE's separation of the task/verification contract from the agent/harness that executes it (so "models and trainers are replaceable" while "scientific content is reusable") is a clean architectural precedent that validates Symphysis's own Agent Card design direction (an AI panel identified and reproducible independent of which underlying model runs it). Worth citing internally as independent confirmation; Symphysis arrived at this independently and needs no ScienceIDE code. | LOW |
| Append-only audit log for every agent panel response attempt, including malformed responses | `product-review-operational-ontology-sep2026.md` §9.2 | operational-ontology's append-only audit log recording every attempted operation, applied or refused, with actor/action/target/params/status is a directly transferable pattern for logging every agent panel response attempt, including a malformed or out-of-schema response an agent produced, as a first-class, queryable record rather than only a success-path transcript. | MEDIUM |
| A `declarations` object stating the orchestrator's own behavioral choices in one place | `product-review-operational-ontology-sep2026.md` §9.2 | operational-ontology's `declarations` object pattern (one small, enumerable value stating the implementation's own behavioral choices, e.g. `{authority, failureSemantics, reindexing, visibilityDefault}`) is worth borrowing directly: Symphysis could expose an equivalent `declarations` value for methodology choices such as how a missing agent response is handled, how a BWM ranking tie is broken, and which alpha-sweep default is used absent an override, giving a reader or reviewer one place to check "what does this implementation actually do" instead of hunting through prose. | LOW |
| Citable framing for "enforced, not merely advisory" guardrails | `product-review-bendlang-bend-sep2026.md` §12.2 | Bend's `LAWS.bend` mechanism (a declarative invariant file plus a mandatory, mechanically-checked proof gate a coding agent cannot bypass short of disabling the checker outright and leaving a visible trace) is a working, concrete demonstration of the same idea Symphysis's own README already claims ("enforced, not merely documented, permission and guardrail architecture"). Bend's own framing, "`LAWS.bend` is `AGENTS.md` backed by proof," is a precise, citable-as-project-documentation (not scientific-source) articulation worth reusing when Symphysis's own guardrail-architecture documentation next discusses how its enforcement differs from a documentation-only convention. Does not mean adopting Bend as a dependency. | LOW |
| Exact-permutation, small-n statistical pattern for AI-panel-versus-human-panel comparisons | `product-review-agentpick-sep2026.md` §11.2 | AgentPick's pooled-statistics module (`evaluation/pooled.py`: exact sign-flip permutation tests over small n, Holm-corrected p-values across a comparison family, bootstrap confidence intervals) is a directly reusable statistical pattern for Symphysis's own AI-panel-versus-human-panel comparisons, where sample sizes (a handful of expert respondents, a handful of AI agents) are similarly small. The exact-permutation approach, feasible specifically because n is small enough to enumerate all sign assignments, is worth adopting verbatim rather than reaching for a large-sample-only significance test that assumes more data than either project actually has. | MEDIUM |
| Durable Flow modeling for resuming a partially-completed AI panel run after an interruption | `product-review-dex-sep2026.md` §10 | Symphysis's multi-agent panel runs are long-running, multi-step, externally-gated processes not structurally unlike a Dex Flow: each panel agent's elicitation turn could be modeled as a Step, with the overall panel run's aggregate state (which agents have responded, which are pending, which failed and need retry) held as a durable Attribute rather than only in in-memory orchestrator state a crash or restart would lose. A narrower, more speculative fit than the pattern's fit for `creator-flow` (per that project's own enhancement file, Symphysis's runs are typically shorter-lived than a durable-execution engine is usually reached for), but the specific problem of resuming a partially-completed AI panel run without re-querying agents that already answered maps onto Dex's core value proposition closely enough to name explicitly. | LOW |
| Offline replay of historical panel transcripts for testing candidate orchestration strategies | `product-review-dream-rsi-sep2026.md` §7.2 | An AI-panel run is itself expensive (API cost, wall-clock time across many agents and rounds), and once collected, its full transcript is a recorded decision history in essentially the same sense as Dream-RSI's discovery tree. If the orchestrator ever needs to explore many candidate panel-configuration or aggregation-order strategies (which agent responds first, how disagreement is resolved, when to run an extra elicitation round) before committing to one for a real, costly panel run, replaying those candidate strategies against already-collected historical panel transcripts, rather than re-running new, expensive AI-panel sessions for every candidate strategy, is a directly applicable instance of Dream-RSI's core idea. Worth a concrete, medium-priority future-research note in Symphysis's own planning documentation, citing Dream-RSI (arXiv:2609.14858, Zheng et al., 2026, a one-week-old preprint with no released code as of this review) by name. | MEDIUM |
| Calibration methodology and bias-control checklist for AI-panel judgments against human-panel labels | `blog-review-loftwah-gist-sep2026.md` §"symphysis-ai-research-survey-engine" | The gist's discussion of "teaching the system Dean's taste" (a small, owner-labelled reference set of real examples, held-out examples to test calibration rather than memorization, blinded order-swapped comparisons, explicit tracking of preference reversals over time) is a close structural match for Symphysis's own core purpose: calibrating an AI panel's judgments against a human panel's actual labelled preferences (the TrustRouter trust-dimension weighting survey being the concrete existing example). Its caution, "a system that can repeat the training preferences but fails new screens is not calibrated," is a directly transferable framing for Symphysis's own held-out validation methodology, and its bias-control checklist (neutral labels, swapped order, stripped provenance, permitted ties/"insufficient evidence" outcomes) is a concrete, adoptable checklist for any AI-panel elicitation run comparing two model-generated positions. A methodology-borrowing opportunity, not a code dependency. | MEDIUM |
| Typed choice/score judgement shape as a cheap pre-panel sanity check, plus an independent-calibration reminder | `blog-review-pedramamini-gist-sep2026.md` §"symphysis-ai-research-survey-engine" | The `choice`/`score` typed-question shape is a natural fit for the BWM/AHP pairwise-comparison and rubric-scoring steps Symphysis already performs. If Symphysis ever wants a fast, cheap, non-LLM-panel-member "sanity check" pass over a large batch of pairwise comparisons before committing compute to a full multi-model AI-panel run, this tool's `jev rank`/`jev batch` commands are a directly reusable pattern, better mirrored against an open model than adopted as a closed vendor dependency, per `gitops.md` §1. Separately, the gist is a reminder that a decision model's own "calibrated confidence" claim degrades under specific conditions unless independently tested, the same discipline Symphysis's own held-out-validation design already aims for at the pooling-methodology level (verified against a published reference JAGS implementation) and should extend to any per-call confidence score consumed from an underlying model. | LOW |
| BWM/AHP pairwise comparisons reframed as independent, parallel, typed judgements | `blog-review-pjburnhill-gist-typesafe-jev-sep2026.md` §6b | BWM and AHP pairwise-comparison steps ("which of these two criteria matters more, and by how much") are exactly Choice- or Score-shaped judgements: a bounded option set, evaluated independently per pairwise comparison, ideally in parallel across the full comparison matrix rather than serially through one long agent conversation. If Symphysis agents currently extract BWM/AHP judgements by parsing free-text LLM responses, issuing the full set of pairwise comparisons for one agent as independent, typed, confidence-scored judgements (via constrained decoding, not the closed Jev API) and letting deterministic code assemble the comparison matrix is a direct, low-risk refactor target, giving a genuine per-comparison confidence value to weight into the Bayesian hierarchical BWM solver alongside the existing HAWC-BWM alpha-sensitivity sweep. | MEDIUM |

## Opportunities identified (2026-09-26 pass, 16 source reviews)

Scope note: this pass covers the 16 new/updated reviews from the 17-link batch reviewed
2026-09-26 (`product-review-{harnessrouter,neo4jev,anyjev,raven-evermind,
microsoft-iq-solution-accelerator,kglite,kimi-k3-in-c,mini-agi,cli-anything,kev-0.5b,
dev-0.4b,trycua-cua,contrastive-lm-clm}-sep2026.md`,
`blog-review-archerhume-jevs-architecture-unmasked-sep2026.md`, and two August files updated
in place this pass, `product-review-codebase-memory-mcp-aug2026.md` and
`product-review-aws-context-ontology-accelerator-aug2026.md`), grepped for explicit
symphysis mentions and each hit read in full context before inclusion here.

Exactly one genuine, concrete fit surfaced from this batch, independently verified against
Symphysis's own source rather than taken on the source review's word alone:

**Dynamic external-tool discovery, via CLI-Anything's CLI-Hub registry pattern**
(`product-review-cli-anything-sep2026.md` §11). Symphysis's own `src/symphysis/tools/
registry.py` was read directly to check the review's claim: `build_registry()` currently
constructs a fixed, hardcoded set of tools per agent run (`rag_retrieval`, `knowledge_repo`,
`web_search`, `citation_verify`, and conditionally `instrument_submit`), gated only by
whether the agent's own Agent Card declares the matching capability, with no lookup-by-name
or dynamic-discovery path for a tool not already known to this module at agent-run
construction time. This confirms the review's claim is accurate, not force-fitted:
CLI-Anything's CLI-Hub (a single command to browse, install, and invoke a wrapped
application's harness by name from a shared registry) is a reasonable reference design if
Symphysis's agents are ever given the ability to discover and invoke an external tool not
already wired into `registry.py` at construction time, rather than continuing to require a
code change in this module for every new tool. Priority: LOW, since Symphysis's current
fixed-roster design is a deliberate, working choice (per the module's own docstring, every
tool's `ToolSpec` wraps a retriever `Agent.__init__` already built, and adding true dynamic
discovery would be a real architectural change, not a drop-in addition), not a gap causing
any known problem today.

No other genuine fit was found. The remaining 15 reviews in this batch either name
symphysis explicitly as a checked, no-fit case, or omit it entirely from their own
cross-project sections: `product-review-neo4jev-sep2026.md` §"cross-repo" ("no direct
architectural overlap found"), `product-review-microsoft-iq-solution-accelerator-sep2026.md`
§"Applications to VERITAS" ("no direct applicability found... shares no architectural surface
with this repository's supply-chain/RAG/workflow scenario"), `product-review-kglite-sep2026.md`
§"Applications to VERITAS" ("no direct fit identified... has no graph-database or
ontology-validation surface that KGLite's feature set would plug into"),
`product-review-kimi-k3-in-c-sep2026.md` §"Applications to VERITAS" (no obvious use for a
single-model C inference engine; the one plausible exception named is
`fca-guided-ontology-gen-llms`, not symphysis), `product-review-mini-agi-sep2026.md`
§"Applications to VERITAS" ("does not map onto... symphysis-ai-research-survey-engine's
multi-agent elicitation focus... closely enough to justify inclusion"),
`product-review-dev-0.4b-sep2026.md` §"Applications to VERITAS" ("no concrete, already-present
need... flagged here for completeness rather than force-fit"), and
`product-review-harnessrouter-sep2026.md`, `product-review-anyjev-sep2026.md`,
`product-review-raven-evermind-sep2026.md`, `blog-review-archerhume-jevs-architecture-unmasked-sep2026.md`,
`product-review-kev-0.5b-sep2026.md`, `product-review-trycua-cua-sep2026.md`,
`product-review-contrastive-lm-clm-sep2026.md`, `product-review-codebase-memory-mcp-aug2026.md`
(2026-09-26 update section), and `product-review-aws-context-ontology-accelerator-aug2026.md`
(2026-09-26 update section), none of which mention symphysis anywhere in their text at all.
Recorded here so a future pass does not re-investigate the same non-fits.

---

## Update, 2026-09-26 (second 10-link batch, 9 source reviews)

- **Evidence-gated acceptance of an agent-panel's elicitation response, directly applicable to
  symphysis's own BWM/AHP/Delphi engine**: T2D-Bench's Evidence Gate (a deterministic rule
  engine checking whether an LLM output cites required, graph-derivable evidence identifiers,
  rejecting or triggering a constrained rewrite when it does not) is architecturally close to a
  real gap in symphysis's own design: when an AI agent stands in for a human expert in a
  Best-Worst-Method, AHP, or Delphi round, nothing currently verifies that the agent's stated
  pairwise judgment or ranking is actually grounded in its own declared RAG corpus rather than
  an ungrounded guess presented with confident phrasing. A T2D-Bench-style gate, checking that
  an agent's elicitation response cites specific passages or facts from its assigned corpus
  before the response is accepted as calibration data, and requesting a constrained rewrite
  naming exactly what evidence is missing when it does not, is a directly transferable pattern
  for improving the reliability of symphysis's underlying data, which matters directly since
  symphysis is "the engine behind TrustRouter's own AHP-weighted dimension-calibration work"
  per this file's own opening description: an evidence-gated elicitation pipeline would improve
  the trustworthiness of numbers that eventually feed VERITAS's own trust-scoring weights
  (`product-review-t2d-bench-sep2026.md` §9.1). | HIGH |
- **AutoHarness's reflector/promoter separation as a candidate self-tuning loop for symphysis's
  own Agent Library**: AutoHarness splits a reflection process (observes sessions, drafts
  candidate rule/skill changes) from a promoter process (validates and applies them), kept
  structurally apart so a bad reflection cannot self-apply. Symphysis already has a shipped
  Agent Library of agent definitions with declared permissions/guardrails and per-agent RAG
  corpora (per this project's own memory record of the Aug-3 rebrand and feature batch); over
  many elicitation panels, some agent definitions will likely prove systematically
  over-confident, under-informative, or poorly calibrated against real BWM/Delphi outcomes.
  AutoHarness's reflect-then-promote separation is a directly transferable structural pattern
  for a future symphysis feature that observes panel outcomes and proposes (but does not
  silently auto-apply) agent-definition refinements, keeping a human or a separate validation
  gate in the loop before any change reaches the live Agent Library
  (`product-review-autoharness-sep2026.md` §9). | MEDIUM |

No other review from this batch (SEPAGen/SynSEPA, doximity/mvcc, stable-worldmodel,
TaskTrooper, Univer, Humyn Labs BRIDGE ASR 2.0, Abide) has a fit for symphysis's own
multi-agent expert-elicitation domain; each was checked against the project's own stated scope
(BWM/AHP/Delphi instruments run against a did:key agent panel with per-agent RAG corpora)
before being ruled out.

## Update, 2026-09-27 (5-link batch: CLM-v0.1-8B, intentional-arrangement-skos, NV-Reason-CXR, NV-Reason-CT, Dormice)

Scope: 5 links resolving to 5 review topics. Two are updates appended to existing reviews (CLM's Hugging Face model repository into `product-review-contrastive-lm-clm-sep2026.md`; a 107-commit re-review into `product-review-intentional-arrangement-skos-aug2026.md`) and three are new reviews. Written without any Agent/Task subagent. Only these 5 topics were rechecked here.

- **A three-condition reader-study design for measuring whether showing an AI panel's reasoning changes human experts' judgments.** Both NV-Reason papers compare (1) no AI, (2) AI labels only, and (3) full AI reasoning plus a structured report, with a fixed 5-point Likert instrument in three blocks (accuracy/reasoning quality, time/efficiency, trust/confidence), including items such as "the AI did not bias me toward incorrect conclusions." Symphysis's HAWC-BWM methodology blends human and AI-agent responses. The same design answers a question symphysis has not yet measured: does a human expert who sees the AI panel's *reasoning* (versus only its weights) move toward or away from the panel, and with how much confidence? Fix the flaw both papers admit: they always ran the unaided condition first on the same case, so recall effects inflate the benefit. Counterbalance condition order or use disjoint case sets per condition (`product-review-nv-reason-cxr-sep2026.md` §11.2, `product-review-nv-reason-ct-sep2026.md` §3). | MEDIUM |
- **Low-friction capture of human experts' rationales.** NV-Reason-CXR's annotation tool (narrate by voice, Whisper transcription, an LLM pass to correct domain terminology, optional translation, human edit per short "record") is a practical way to collect the free-text justification behind each human expert's BWM/Delphi answer, which is usually the part experts skip when forced to type. Multilingual support fits Spanish-speaking panellists. The captured rationales then become the human side of any human-vs-agent reasoning comparison (`product-review-nv-reason-cxr-sep2026.md` §2, §8.3). | MEDIUM |
- **CLM `Score` as a cheap rating/justification consistency flag.** CLM's `Score` question returns a calibrated distribution over an ordinal rubric in milliseconds. Scoring an agent's free-text justification against the same 1-9 scale it rated on, and flagging large disagreements, gives a fast secondary check that an agent's number is supported by its own stated reasons. Use it as a flag for review, never to overwrite the agent's answer. Constraints from the 2026-09-27 update: the heads are locked to a Qwen3-8B encoder served by vLLM (2048-token default context), and the checkpoint is a pickle file that must be revision-pinned and converted to `safetensors` before use (`product-review-contrastive-lm-clm-sep2026.md` Update U.1 to U.3). | LOW |
- **Persistent per-agent workspaces, only if agents start executing code.** If symphysis agents ever run analysis code (sensitivity analyses over their own weights, for example), Dormice's idempotent `acquireSandbox(key)` keyed by the agent's did:key gives each agent a gVisor-isolated workspace that survives across Delphi rounds and costs almost nothing while idle. It speaks the E2B protocol, so the E2B Python SDK works unchanged. Not needed while agents only produce text (`product-review-dormice-sep2026.md` §10.2). | LOW (conditional) |
- **A headless-browser smoke test as a pre-commit gate for the React/FastAPI UI**, following intentional-arrangement-skos's new `tools/smoke.py` (serve on an ephemeral port, assert the main form renders fully with a clean console, round-trip an export/import). Symphysis has already shipped one real chart-rendering crash (the Aug-2 `np.mean`/`np.percentile` mismatch fix, from before the rebrand); a smoke test that loads a results page with charts is the kind of gate that could have caught it before release (`product-review-intentional-arrangement-skos-aug2026.md` Update U.3 item 4). | LOW |

## Update, 2026-09-29 (literature applicability, Sep-27 to Sep-29 paper intake)

Scope: this section comes from papers catalogued into the VERITAS academic literature catalogue between 27 and 29 September 2026, not from repository reviews, so there is no `product-review-*.md` behind each item. The fits from the 27-28 September intake were identified on 28 September but never written here; they are included now. Written without any Agent/Task subagent.

- **Replace plain majority voting in panel aggregation with a reliability- and correlation-aware aggregator.** Debate or Vote, Choi et al., 2025, arXiv:2508.17536 (NeurIPS 2025) shows that majority voting accounts for most of the gains usually credited to multi-agent debate and proves that debate alone forms a martingale over beliefs, so extra Delphi rounds do not raise expected correctness without a corrective bias. Beyond Majority Voting, Ai et al., 2025, arXiv:2510.01499 (preprint) gives training-free aggregators that weight agents for heterogeneity and correlated errors, and When Agents Disagree, Chen et al., 2026, arXiv:2609.11709 (preprint) uses Bayesian backward reasoning as a label-free anchor, with its largest gains on the questions where agents disagree. Symphysis already blends AI-agent and human responses; weighting agents by estimated reliability and error correlation (agents built on one base model are correlated) is a direct upgrade over treating every agent as an independent vote. | HIGH |
- **A claim-level citation check before any generated report or survey section is accepted.** Cited but Not Verified, Onweller et al., 2026, arXiv:2605.06635 (preprint) finds that deep-research agents keep link validity above 94% yet reach only 39 to 77% factual accuracy against the sources they cite, and that raising research depth from 2 to 150 tool calls lowers fact-check accuracy by about 42%. LLM hallucinations in the wild, Zhao et al., 2026, arXiv:2605.07723 (preprint) estimates 146,932 non-existent citations in 2025 papers alone, and Correctness is not Faithfulness in RAG Attributions, Wallat et al., 2025, DOI 10.1145/3731120.3744592 shows models citing planted documents they did not rely on in more than half of adversarial trials. A verification stage that resolves each reference (DOI or arXiv lookup) and checks each cited sentence against the retrieved source text should gate symphysis's survey output. | HIGH |
- **Order-swapped judging wherever an LLM adjudicates between agent answers.** Judging the Judges, Shi et al., 2025, DOI 10.18653/v1/2025.ijcnlp-long.18 shows capable judges have systematic, task-dependent position bias. Run each pairwise judgement in both orders and treat order-dependent verdicts as ties. JEV-as-a-Judge, Li et al., 2026, arXiv:2609.26550 (preprint) adds a cheap accept-or-escalate pattern that hands only hard cases to the stronger judge. | MEDIUM |
- **Guard Delphi feedback rounds against sycophantic drift.** XYEval, Wu et al., 2026, arXiv:2609.23939 (preprint) shows agents adopting misleading suggestions instead of recognising the misdirection, with relative drops up to 46.7%, and a warning instruction only partly helps. When agents see the group summary or a facilitator's framing between rounds, log each agent's pre-feedback answer and report how far agents moved toward the summary, separately from whether they moved toward the truth. | MEDIUM |
- **Mixed-model panels, with communication treated as a tunable cost.** Self-Organizing Agent Teams, Pappu et al., 2026, arXiv:2609.22682 (preprint) reports heterogeneous teams at 66.7% against 56.0% for homogeneous ones, while Scaling Discovery through Test-Time Communication, Park et al., 2026, arXiv:2609.21032 (preprint) finds that communication hurts in 7 of 25 games. Instrumental Choices, Wiedermann-Möller et al., 2026, arXiv:2605.06490 (preprint) shows behavioural propensities varying by model family, a further reason to mix families. | MEDIUM |
- **Stage-specific rubrics for planning, evidence, review and synthesis.** RubricEM, Li et al., 2026, arXiv:2605.10899 (preprint) decomposes long-form research into rubric-guided stages and its 8B model approaches proprietary deep-research systems on four benchmarks. The rubric-per-stage structure is usable as an evaluation scheme for symphysis runs even without the reinforcement-learning part. | MEDIUM |
- **Organisation-scale orchestration only as a reference.** Agensh, Zhan et al., 2026, arXiv:2609.26781 (preprint) scales to 1,024 agents with a shared claim-and-merge workspace; the scale is far beyond an expert panel, so it is a design reference rather than a recommendation. | LOW |

## 2026-09-30: Reasoning traces and experiment test bench

Recorded as §9 of `docs/architecture/governance-layer-and-runtime-backends-plan.md` rather than
duplicated here: provider-by-provider reasoning capture, one OTel-GenAI-named event record per step,
and an ordered roadmap for turning Symphysis into a condition x model x dataset x seed test bench.
Reuses the existing Langfuse, AgentSight, OpenAI Evals and AutoHarness reviews; adds Inspect AI as
the main design reference (not a dependency).
