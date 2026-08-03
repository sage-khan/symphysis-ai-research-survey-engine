# Changelog

All notable changes to Symphysis (formerly SAGE, formerly agentic-survey-tool). Bug fixes and their root causes
are tracked separately in `diagnostics.md`.


## 2026-08-03 (Python packaging + CLI plan)

- New `docs/packaging-plan.md`: a step-by-step plan for making `agentic_survey` a real
  installable PyPI package (`pyproject.toml`, dependency/extras split, versioning) and giving
  `symphysis` a proper CLI entry point beyond its current single `run` subcommand (`new`,
  `add-agent`, `report`), plus a publish-on-tag CI job using PyPI's trusted-publisher OIDC flow.
  A plan to review, not yet implemented. README's "Packaging" section now points to it.


## 2026-08-03 ("?" help tooltips for non-technical users)

- New `HelpTooltip.jsx`: a small clickable "?" icon that pops a plain-language explanation next
  to it, for exactly the fields a non-technical user would otherwise have to guess at.
- Applied to `AgentForm.jsx`'s most jargon-heavy inputs (temperature, max tokens, seed, sampling
  repeats, RAG-augmented, web search, guardrail denylist patterns) and to the results table's
  most jargon-heavy output (the Bayesian weight table's "Mean" and "95% CI" columns).
  Deliberately scoped to the fields most likely to confuse a non-technical reader rather than
  every input across the whole app; the rest of the UI's fields already carry a plain-language
  `mono-dim` description line beneath them (see `role_pack`, `rulefile`, `system_prompt_override`
  for examples of that existing pattern), so a tooltip there would be redundant.


## 2026-08-03 (fix: an in-flight agent was misreported as "skipped")

- `analytics.py`'s `compute_analytics()` now distinguishes an agent that genuinely errored out
  before producing a result (`skipped`) from one that simply hasn't finished yet because the
  survey is still running (new `in_progress` status), via a new `is_running` parameter the
  `/analytics` endpoint now passes from the current run-status. Both looked identical on disk
  before this fix (no `result.json`), which misreported normal in-flight progress as failure
  throughout this session's slower runs. The live progress panel and Analytics tab render
  `in_progress` distinctly (amber) from the red "Skipped" state.


## 2026-08-03 (launch-readiness: LICENSE, CITATION.cff, CONTRIBUTING.md)

- `LICENSE`: the real, unmodified Apache License 2.0 text (copied from a genuine
  GitHub-picker-generated Apache-2.0 LICENSE already in use on another of the author's own
  repos, byte-identical except the filled-in copyright line, rather than reconstructed from
  memory, per the standing instruction to use GitHub's own generator text rather than
  hand-write it).
- `CITATION.cff`: a Citation File Format entry so GitHub renders a "Cite this repository"
  button and gives anyone citing Symphysis in a paper (starting with the TrustRouter/BSI paper
  itself) the exact author, title, and version to use.
- `CONTRIBUTING.md`: how to run the test suite and linter (the exact commands CI runs), the
  documentation-update-in-the-same-change rule, and where to file issues.
- README: links to all three from the top of the file.
- Repository is not yet public; GitHub repo metadata (description, topics, social preview
  image) still needs setting manually via GitHub's own UI, since this session has no working
  GitHub API/CLI credentials to set it programmatically.


## 2026-08-03 (docker/ -> infrastructure/docker/, infrastructure/kubernetes/ reserved)

- `docker/Dockerfile` moved to `infrastructure/docker/Dockerfile`; `infrastructure/kubernetes/`
  added (currently a placeholder, no manifests yet) for a future Kubernetes deployment. Matches
  the convention `project-cogtwins` already uses (`infrastructure/fabric-poc/...`).
  `docker-compose.yml`'s `build.dockerfile` and the README's repository-structure tree and
  "Future enhancements" section updated to match; `docker compose config -q` verified clean.


## 2026-08-03 (getting-started walkthroughs; fixed a domain-hardcoded default prompt)

- New `docs/getting-started.md`: two runnable, verified walkthroughs (a zero-setup
  manual-provider survey with no external accounts needed, the same survey against a real
  local Ollama model), plus the equivalent web UI flow including linking a knowledge base to
  an agent. Both CLI walkthroughs were actually run end to end while writing this, not just
  described.
- Fixed a real bug found while writing the walkthrough with a deliberately non-construction
  example survey: `config/prompts/expert_panel_system.txt`, the shared default every agent
  falls back to unless it names its own template, told every agent in every survey it was
  doing "a construction-industry blockchain suitability framework (the Blockchain Suitability
  Index, BSI)" regardless of the actual survey. Genericized; see diagnostics.md.


## 2026-08-03 (BSI as the first real, tested use case for reusable knowledge bases)

- Created six real, populated knowledge bases via the new API (Blockchain Trust & Attack
  Resistance, Data Quality & Polyglot Persistence, BIM & Digital Building Logbooks, GDPR & Data
  Governance, Structural Health Monitoring & Digital Twins, Construction Project Management &
  MCDM), each seeded with the same real, cited content already written for
  `bsi-hawc-bwm`'s per-role RAG corpora, so this feature has a genuine populated example rather
  than an empty shell the first time anyone opens the Knowledge Bases tab. The survey's own
  corpora are untouched; these are separate, reusable copies under `agents_library/knowledge_bases/`
  future agents (in this or any other survey) can link to directly instead of re-uploading.


## 2026-08-03 (live progress panel while a survey is running)

- SurveyDetailPage now shows a progress panel while a run is in flight: a percentage bar
  ("N of M agents attempted") plus a colored chip per agent (waiting / contributed / zero
  accepted / skipped), polled every 2 seconds alongside the existing run-status poll. Derived
  from the same `/analytics` classification the Analytics tab already computes from what's
  actually on disk (an agent counts as "attempted" once it has moved out of `not_run`); no new
  backend endpoint needed. Previously the only run-in-progress feedback was the sidebar's
  spinner/"Running..." label, with no visibility into which agents had finished or how many
  were left, which mattered in practice on this session's own long qwen2.5:32b runs.


## 2026-08-03 (Swagger/OpenAPI documentation description)

- `web/backend/main.py`'s FastAPI app now has a real `description` (previously blank),
  shown on the auto-generated `/docs` (Swagger UI) and `/redoc` pages, which were already live
  and functional (FastAPI generates them automatically) but undocumented in this README.
  README: new "API documentation" section pointing to `/docs`, `/redoc`, and `/openapi.json`.


## 2026-08-03 (reusable knowledge bases; L1 self-comparison rule restated per level; latent RAG permission gap fixed)

- New `agents_library/knowledge_bases/<kb_id>/`: named, reusable domain-knowledge collections,
  upload once (`.md`/`.txt` as-is, `.pdf`/`.docx` converted to `.md` on upload, matching the
  existing per-survey `knowledge_repo` upload pattern), reuse across any agent by pointing its
  `rag.corpus_path` at the same directory instead of re-uploading the same files into a one-off
  per-agent corpus every time. New `web/backend/routers/knowledge_bases.py`
  (list/create/delete a knowledge base, list/upload/delete its files) and a new "Knowledge
  Bases" tab on the Agent Library page (`KnowledgeBasesTab.jsx`) for managing them without
  touching a JSON file by hand.
- `AgentForm.jsx`'s RAG section now offers a dropdown of existing knowledge bases (selecting
  one sets `corpus_path` to that knowledge base) alongside the existing free-text path field,
  addressing that RAG configuration previously offered only an enabled/disabled checkbox plus a
  path an operator had to already know and had no way to populate through this app.
- Fixed a latent gap in the same form: saving a RAG-enabled agent never added a matching entry
  to `permissions.data_scopes`, so any agent actually created through this form (rather than by
  hand-editing a JSON card, which is how every real agent card in this repo so far was
  authored) would fail at run time with a permission error the moment it tried to read its own
  configured corpus. `handleSave` now derives and appends the needed `<corpus_path>/**` scope
  automatically if the agent's own scopes don't already cover it.
- `instruments/hierarchical_bwm.py`'s per-level task template now restates the
  self-comparison-is-1 rule inline for every level, not just a pointer back to the shared intro
  (see diagnostics.md: even qwen2.5:32b still rated Best-to-itself as 9 specifically on L1 with
  only the intro-level statement).


## 2026-08-03 (survey rulefile rewritten for the real hierarchy; real input documents; reputable-source-only rule)

- `surveys/bsi-hawc-bwm/rulefile.md` was still describing the old flat
  six-dimension survey (wrong glossary scope, a reference to the removed
  weighting/human_responses_path stanza). Rewritten to describe the real
  seven-level hierarchy, list the actual reference material every agent
  in this survey now has access to, and explain the two-stage
  gate-then-score architecture.
- Added two more real documents to this survey's shared knowledge_repo:
  `bsi_expert_questionnaire_v5_real_survey_instrument.md` (the actual BSI
  Expert Questionnaire, v5 May 2026, as administered to the real 15-expert
  human panel via LimeSurvey 185662, copied verbatim, not paraphrased) and
  `trustrouter_research_hypothesis.md` (an extract of the TrustRouter
  construction paper's own stated research gap and contribution, framing
  what this survey's weight elicitation is actual evidence for or
  against). The rulefile now tells every agent explicitly what these
  documents are and where to find them.
- `config/global_rulefile.md`: new rule 1.4, citing only real, verifiable,
  reputable sources (peer-reviewed papers, labelled preprints, standards
  bodies, academic/institutional reports); never a blog, marketing page,
  forum thread, or wiki, even if the claim happens to be true.


## 2026-08-03 (agent-table column order, sidebar tagline swap)

- The Agents tab (per-survey), the Agent Library page, and both Analytics
  tables (per-sample "who said what" and "Non-contributing agents") now
  list display name before the raw agent id, matching how a human reads
  the table (a friendly name first, the machine identifier second).
  `web/backend/analytics.py`'s per-agent entry now includes `display_name`
  so the Analytics tables can show it too, not just the Agents tab (which
  already got it from `/api/surveys/<id>/agents`).
- Sidebar: removed "v0.1.0 . control panel" from the top (moved to the
  bottom, where the tagline used to be) and removed the "Config-driven
  agent panels for expert-elicitation surveys" tagline entirely.


## 2026-08-03 (bsi-hawc-bwm survey converted to the real full hierarchy; real knowledge grounding; Agent Library populated)

- `surveys/bsi-hawc-bwm/survey.yaml` now uses `instrument: hierarchical_bwm`
  with the complete real seven-level TrustRouter structure (L1 through
  L3e), the exact criterion descriptions from `trustrouter.py`, and the
  real composite formula string, replacing the old flat six-dimension
  `bwm` survey that only elicited DVS's internal weights while looking, to
  anyone reading its title or results, like a complete TrustRouter
  elicitation. Every existing agent card's own descriptive `instrument`
  field was updated to match (this field is display-only; `survey.yaml`
  alone decides which instrument actually runs, but a stale value there
  was misleading). The unused `weighting`/`human_responses_path` stanza,
  which pointed at a file literally named `experts.SYNTHETIC.json`, was
  removed along with that file: `hierarchical_bwm` surveys don't (yet)
  wire in the HAWC-BWM human-panel combination flat `bwm` surveys use, so
  keeping synthetic data referenced from a survey meant to produce real
  results was misleading, not merely unused.
- Deleted the separate `trustrouter-agent-panel-live-20260803` survey (the
  actual completed 17-agent live run from earlier this session): it ran
  the same incomplete flat six-dimension calculation and its report
  presented that as a finished "live multi-agent panel" result. Backed up
  to the veritas server's `~/backups/` before deletion, not merely
  discarded.
- New `surveys/bsi-hawc-bwm/knowledge_repo/trustrouter_concept_paper_primer.md`:
  every agent in this survey (RAG-enabled or not, this directory is
  retrieved automatically for the whole panel) now receives a primer
  derived directly from `trustrouter.py` and `TRUSTROUTER_EQUATION.md`
  explaining the two-stage gate-then-score architecture, why the L1
  comparison (DVS/F/E/A) is a different kind of "importance" than every
  other level because those four combine multiplicatively rather than as
  a weighted sum, and where the previously-missing F/E/A branches and
  their own sub-criteria fit. Earlier runs of this survey had no such
  primer and, per the user's own reading of prior results, produced
  reasoning that treated the six DVS dimensions as the entire calculation.
- Populated six of this survey's seven RAG corpora (`blockchain-engineer`,
  `data-engineer`, `bim-coordinator`, `compliance-officer`,
  `structural-engineer`, `project-manager`), which previously held only an
  empty template `SOURCES.md` and no retrievable content despite
  `rag.enabled: true` on the matching agent cards, meaning those agents
  were not actually grounded in anything. Content is copied and cited from
  `LITERATURE_REVIEW_CATALOG.csv` in the project's own literature bank
  (never fabricated), one real, cited source set per role directly
  relevant to that role's slice of the TrustRouter hierarchy (blockchain
  attack-resistance and the oracle problem for `blockchain-engineer`, ISO
  25012 data quality and polyglot persistence for `data-engineer`,
  Digital Building Logbooks and BUILDCHAIN for `bim-coordinator`, GDPR and
  the blockchain-immutability tension for `compliance-officer`, structural
  health monitoring and digital twins for `structural-engineer`,
  construction project management and MCDM method comparison for
  `project-manager`). Web search was considered per the standing
  instruction to ground agents via web search or the literature bank, but
  `TAVILY_API_KEY` is not configured on the veritas server, so the
  `web_search` tool remains disabled on these agents for this run; that
  gap is noted here rather than left silent.
- `agents_library/` (previously empty, the reason the web UI's Agent
  Library panel had nothing in it) now has 11 reusable Agent Cards: the
  six TrustRouter-relevant roles' base (non-RAG) variants, each tagged
  with the closest matching standard role knowledge pack
  (`blockchain_trust_specialist`, `data_engineer`, or
  `construction_engineer` for the four construction-adjacent roles), plus
  the five-model independent-reviewer roster (Claude Opus/Sonnet/Haiku,
  and manual-paste-in Gemini/GPT). The RAG variants were not copied into
  the library: their `corpus_path`/`data_scopes` are specific to
  `bsi-hawc-bwm`'s own corpus directories and would silently point at the
  wrong (or a missing) corpus if assigned into a different survey without
  editing first.
## 2026-08-03 (hierarchical BWM: the real TrustRouter formula structure)

- The flat, six-dimension BWM survey previously used for TrustRouter/BSI
  weight elicitation covered only one branch (DVS's own sub-dimensions) of
  the real framework. The actual TrustRouter composite is
  `TrustRouter = DVS x F x (1 + E) x A` across four top-level factors, three
  of which (DVS, A, E) are themselves broken down by their own separate
  BWM comparison, and one of DVS's own six dimensions (Q) is broken down
  by a third level again (see `trustrouter.py` in the BSI survey-app for
  the authoritative structure). Treating the six-dimension survey as "the"
  TrustRouter calculation was incomplete.
- New `src/agentic_survey/instruments/hierarchical_bwm.py`: a survey
  defines multiple named BWM comparison levels, each over its own subset
  of criteria, with a `parent_level`/`parent_criterion` on any level that
  elaborates another level's criterion. An agent completes every level in
  one structured JSON response (one call, same as `bwm`/`ahp`; no change
  needed to `Agent`, `guardrails.py`, or `storage.py`).
- New `src/agentic_survey/solvers/hierarchical_bwm.py`: solves each level
  independently (classical + Bayesian BWM, same solvers `bwm` already
  uses), then computes each leaf criterion's global weight by multiplying
  local weights up its ancestor chain. The root level's own weight is
  deliberately excluded from that multiplication: verified directly
  against TrustRouter's real, published numbers
  (`TRUSTROUTER_EQUATION.md`), L1's DVS/F/E/A weights express relative
  importance among factors combined multiplicatively at the very top, not
  shares of one linear sum, so multiplying a deeper leaf's weight by L1's
  own weight would conflate two different kinds of importance. This was
  confirmed by reproducing the exact published global leaf weights
  (IQ 0.0615, CQ 0.0629, T_source 0.0654, and so on) from the same local
  level weights, not by assumption.
- `orchestrator.py`'s `INSTRUMENTS` registry now has three entries
  (`bwm`, `ahp`, `hierarchical_bwm`); new `render_hierarchical_bwm_report`/
  `render_hierarchical_bwm_charts` in `reporting.py` show the composite
  formula, every level's own solved weights, the populated equations
  (`DVS = 0.185*Q + ...`, in the same form as the real reference
  document), and the global leaf weights table.
- 12 new tests, including one that reproduces the real TrustRouter
  numbers exactly from the real level structure, and a full end-to-end
  orchestrator test running all seven real TrustRouter levels through a
  manual-provider agent; 159/159 pass repo-wide.
- Also: removed the "01/02/03" numbering glyphs from the sidebar
  navigation, fixed the Analytics "who said what" table's reasoning
  column (was CSS-truncated to one line with an ellipsis, relying on a
  hover tooltip for the rest; now wraps and scrolls in place), added a
  manual refresh button plus 8-second auto-poll to the Analytics tab
  (it reflects a panel that a run in another tab or a still-in-progress
  run can change at any moment), an explicit `Cache-Control: no-store` on
  every API response, and fixed the backend's FastAPI app title, which
  still said "SAGE API" from before this project's second rename.

## 2026-08-03 (concept-driven survey creation)

- New `web/backend/survey_proposer.py` and `POST /api/surveys/propose-concept`:
  given a plain-language study description, an LLM call proposes a title,
  a one-sentence description, an instrument choice (`bwm` or `ahp`) with
  its reasoning, and a criteria list, an LLM call that writes nothing to
  disk. Mirrors `agent_proposer.py`'s propose-then-approve shape, applied
  to the survey itself rather than its agent panel.
- The New Survey form gains a third mode, "Describe your study", alongside
  the existing document-upload and manual-entry modes: a concept textarea
  plus provider/model pickers, a "Propose" button that populates the same
  editable title/description/instrument/criteria fields the other two
  modes already use, so the review-before-creating step is identical
  regardless of how the draft was produced.
- 10 new tests (parser validation, a faked-provider unit test, and an
  HTTP-level FastAPI TestClient test covering both a successful proposal
  and a 502 on an unparseable response); 147/147 pass repo-wide.

## 2026-08-03 (richer, self-contained survey reports)

- Every survey report now gets two generated sections appended after the
  solved-weights table: a Methodology section (which instrument ran, how
  many agents contributed, what genuineness checks ran on every agent's
  QA precheck and cited sources, a pointer to the SHA-256 integrity
  manifest) with that survey's chart images embedded inline via relative
  paths, and a Per-agent detail section listing every contributing
  agent's role, model, DID, QA precheck pass or fail, cited sources, its
  full answer, and its complete reasoning text, not only the aggregated
  numbers.
- `orchestrator.py` now captures each accepted sample's reasoning,
  sources_used, and the owning agent's QA precheck result (loaded once
  per agent, `None` for manual-provider agents which skip the automated
  precheck) alongside the existing per-sample metadata, threaded through
  to the new report sections. Shared across both `bwm` and `ahp`
  instruments rather than duplicated per instrument.
- Because the chart images are embedded with paths relative to
  `report/report.md`, the existing `.zip` download is now a genuinely
  self-contained bundle: extract it and `report.md` renders correctly,
  images included, in any offline Markdown viewer, no copy of this
  application required.
- 7 new tests, plus the existing end-to-end AHP orchestrator test
  extended to assert the new sections actually appear in a real run's
  output; 137/137 pass repo-wide.

## 2026-08-03 (AHP instrument and multi-method solver registry)

- New `src/agentic_survey/instruments/ahp.py`: the Analytic Hierarchy
  Process instrument (Saaty, 1980). Prompts an agent for an upper-
  triangular pairwise comparison matrix on Saaty's 1-9 scale over the
  survey's criteria, the same `sources_used` citation instruction and
  closed-vocabulary verification BWM already has, and validates every
  comparison is a positive number covering every required pair before
  accepting a response.
- New `src/agentic_survey/solvers/ahp.py`: classical AHP, priority weights
  via the principal eigenvector of the comparison matrix, consistency
  ratio via Saaty's random index table, flagged for review above the
  standard 0.10 threshold; `aggregate_individual_priorities` combines
  multiple agents' independently solved weight vectors via geometric mean
  (Forman and Peniwati, 1998), the same "each agent is one complete,
  independent data point" treatment BWM already gives every agent.
- `orchestrator.py`'s `INSTRUMENTS` registry now has two entries
  (`bwm`, `ahp`); the classical-plus-Bayesian BWM solving path and the
  new AHP solving path are each their own function, so adding a further
  method (Delphi, TOPSIS, and the rest of the candidates in README's
  Future Enhancements) means one new `Instrument`, one new
  `_solve_<name>` function, and one registry entry, with nothing else in
  the orchestrator, `Agent`, or `storage.py` needing to change.
- New `render_ahp_report`/`render_ahp_charts` in `reporting.py`: an AHP
  survey's report shows the aggregated priority weights, each agent's own
  consistency ratio, and a bar chart, kept separate from the BWM/HAWC-BWM
  report renderer rather than overloading its Bayesian-specific shape.
- The New Survey form's instrument picker now offers AHP alongside BWM.
- 18 new tests (`test_ahp_instrument.py`, `test_ahp_solver.py`,
  `test_orchestrator_ahp.py`, the last a full end-to-end run through two
  manual-provider agents, aggregation, report, and integrity manifest);
  131/131 pass repo-wide. The solver itself is verified against a
  hand-constructed perfectly-consistent matrix with known weights
  (recovers them exactly) and a deliberately cyclic, wildly inconsistent
  matrix (correctly flagged, CR > 0.10).

## 2026-08-03 (integrity manifest, three-tier rulefiles, architecture diagrams)

- New `src/agentic_survey/integrity.py`: a SHA-256 hash of every file a
  survey run produced, computed once right after the run finishes, plus a
  single root hash summarizing all of them, plus a plain `SHA256SUMS` file
  in the exact format `sha256sum -c` already understands. A reviewer can
  verify a survey folder was not altered since the manifest was generated
  using nothing but coreutils, no copy of this application required.
  `GET /api/surveys/{id}/integrity` returns the stored manifest;
  `GET /api/surveys/{id}/verify-integrity` recomputes every hash right now
  and reports an honest pass/fail with exactly what changed, was added, or
  was removed. Surfaced in the Results tab; included automatically in the
  existing `.zip` download since it lives inside the survey folder like
  every other output file. 13 new tests.
- Rulefiles are now a three-tier hierarchy, broadest to narrowest: the
  global rulefile (every agent, every survey), a new survey-level
  rulefile (`surveys/<id>/rulefile.md`, every agent in one survey,
  editable from that survey's Knowledge tab), and the existing per-agent
  rulefile. All three are appended to an agent's system prompt in that
  order. The global rulefile was rewritten from five bullet points into a
  structured, publication-citable document (genuineness and
  anti-fabrication, scope discipline, configuration integrity, reasoning
  transparency, independence and non-collusion). The `bsi-hawc-bwm`
  survey's own rulefile now documents what each of its six TrustRouter/BSI
  dimensions actually means and why they should not be treated as
  interchangeable with generic data-quality criteria. 2 new tests.
- New `docs/architecture/` with three draw.io diagrams (source plus
  rendered PNG, per this repo's diagram convention):
  `current-system-architecture` (the real six-stage pipeline as
  implemented today), `agent-card-anatomy` (the Agent Card's nine field
  categories), and `target-pipeline-vision` (the longer-term
  researcher-workflow vision, every stage color-coded implemented,
  partially implemented, or planned, so the diagram cannot be misread as
  a claim that unimplemented stages already exist).

## 2026-08-03 (CI/CD pipeline, QA genuineness checks, global and per-agent rules)

- New `.github/workflows/ci-cd.yml`: validate (ruff lint, docker-compose
  syntax check), test (full pytest suite), and deploy (SSH into the
  veritas server, recreate the backend container, restart the frontend,
  health-check both) on every push to `main`, modeled on
  project-cogtwins's own CI/CD workflow. Needs `SYMPHYSIS_SSH_HOST`,
  `SYMPHYSIS_SSH_USER`, `SYMPHYSIS_SSH_KEY`, `SYMPHYSIS_SSH_PORT`,
  `SYMPHYSIS_PROJECT_PATH`, `SYMPHYSIS_CORS_EXTRA_ORIGINS`, and
  `SYMPHYSIS_SERVER_HOST` configured as GitHub repository secrets before
  the deploy job can run; validate and test run regardless.
- New `src/agentic_survey/qa_checks.py`: deterministic verification, not a
  further model call. `build_precheck_ground_truth`/
  `verify_precheck_response` compare an agent's restated configuration
  against its real one field by field; `extract_source_tags`/
  `verify_sources_used` compare a response's claimed `sources_used` against
  what reference material was actually present in that prompt.
- `Agent.introduce()` replaced with `Agent.run_qa_precheck()`: still the
  first turn of every non-manual agent's run, but now tells the agent its
  real agent ID, role, model, and which knowledge sources it has
  (dedicated RAG, shared knowledge repo, role pack, web search), and asks
  it to restate that configuration as JSON rather than free prose. The
  restatement is checked field by field against ground truth; any
  mismatch (a hallucinated capability, or a comprehension failure) is
  logged plainly as `qa_precheck.json` and a `qa_precheck` conversation
  entry, not hidden. This directly answers the requirement that agent
  identity/role/model/knowledge-base claims must not be taken on faith.
- `BWMInstrument`'s response schema gains a `sources_used` field: the
  prompt lists the exact reference-material tags actually present (or
  states none were given), and the agent must cite only from that closed
  vocabulary or `general_knowledge`. `storage.write_guarded_run` checks
  every accepted sample's claim against what was truly available and logs
  a `fabricated_source_citation` conversation entry for any citation that
  was never actually provided, surfaced in the Trace viewer.
- New global and per-agent rulefiles: `config/global_rulefile.md` (ships a
  default: never fabricate a source, cite by exact tag, answer only from
  what you were actually given, restate configuration accurately, explain
  real reasoning) applies to every agent in every survey; a new
  `AgentCard.rulefile` field lets one agent add its own rules on top. Both
  are appended to that agent's system prompt. Editable from Settings
  (global) and the Agent form (per-agent), or by editing
  `config/global_rulefile.md` directly.
- README: added a Future enhancements section (candidate MCDM/consensus
  instruments: AHP, ANP, TOPSIS, ELECTRE, classical and real-time and
  fuzzy Delphi, rapid expert consultation, Nominal Group Technique,
  Q-methodology, generalized sensitivity analysis, pilot-testing support,
  inter-rater reliability checks; plus a Linux CLI and a PyPI package as
  packaging goals), a CI/CD note under Deploying, and caught up several
  files that earlier feature work had left undocumented in the "what each
  file does" tables and the "What it does" list (`app_config.py`,
  `role_packs/`, `tools/web_search.py`, `qa_checks.py`, the Agent Library
  and knowledge-repo and natural-language-proposer routers/pages).
- 8 new tests (`tests/test_qa_precheck.py`) covering the QA precheck's
  pass/fail/unparseable-response paths, rulefile injection into the system
  prompt, and the fabricated-source-citation check; 103/103 tests pass
  repo-wide.
- Repo-wide prose cleanup: every ` -- ` and em dash used as a sentence
  connective, across code comments, docstrings, markdown docs, and UI
  text, rewritten with a comma, colon, period, or semicolon per
  `.claude/rules/writing-style.md`'s zero-tolerance rule, including
  several instances the file-type-scoped sweep missed on the first pass
  (`config/defaults.yaml`, `.env.example`, and this repo's own
  `.claude/rules/` files). Three structural exceptions confirmed and left
  alone: `markdown_parser.py`'s and `document_parser.py`'s delimiter
  regexes (detecting a real end-user data-format convention, not
  connective prose) and the npm CLI argument-passthrough syntax in the
  frontend dev-server launch command.

## 2026-08-03 (standard role knowledge packs)

- New `src/agentic_survey/role_packs/` package: eight curated,
  professional-domain knowledge primers (`packs/*.md`) covering AI/ML
  Scientist, Data Engineer, LLMOps Engineer, Knowledge Graph Engineer,
  Construction/Civil Engineer, Wind Energy/SCADA Engineer, Blockchain &
  Distributed Trust Specialist, and Cybersecurity/GRC Specialist, named
  standards, common failure modes, and evaluation heuristics each of
  those professions actually uses, not survey-specific claims. This is
  the standard-role grounding the user asked for so an agent created as
  "Data Engineer" speaks from that standpoint immediately rather than
  from a blank `role_description` alone.
- `AgentCard` gains an optional `role_pack` field (an id, e.g.
  `"data_engineer"`, not a fuzzy match against the freeform `role` text,
  deliberately explicit so a reviewer can see exactly which pack, if
  any, was attached and never has to guess whether a role string was
  matched correctly).
- `Agent` now includes the pack's full body as the first context source
  on every run, ahead of the agent's own RAG corpus, the survey's shared
  knowledge repo, and web search: a fixed professional baseline, not
  something retrieved by relevance, mirroring how a human panelist in
  that role already knows this material walking in rather than looking
  it up per question. Logged via `write_tool_call` like every other
  context source, so a reviewer can see exactly what was injected.
- New `GET /api/role-packs` endpoint (discovers packs from disk, so
  adding a `.md` file is enough to expose a new pack, no code change);
  `AgentIn.role_pack` threaded through both `agents.py` and `library.py`'s
  create/update routes.
- New "Standard role knowledge pack" dropdown on the Agent form (survey
  and library scope both), showing the selected pack's one-line summary.
- `tests/test_role_packs.py` (4 new tests); 82/82 tests pass repo-wide.
- Live-verified: created a real "Data Engineer" agent with
  `role_pack: "data_engineer"`, ran it against mistral:7b, and confirmed
  the pack's actual body text appears in the outgoing `prompt.md`
  labelled `[role knowledge: data_engineer]`. Verified in the browser via
  Playwright (zero console errors) that the picker lists all eight packs
  and shows the right summary on selection. Test survey deleted after.

## 2026-08-03 (agent tools: real web search + shared survey-level knowledge repo)

- New `src/agentic_survey/tools/web_search.py`: real web search via the
  Tavily API (built specifically for LLM-agent tool use). Requires
  `TAVILY_API_KEY`; raises `WebSearchError` (never fabricates a result) if
  it's not set or the request fails.
- `Agent` (`agent.py`) now combines three context sources before every
  prompt, not just RAG: (1) the agent's own dedicated RAG corpus if
  `rag.enabled`, unchanged; (2) the survey's shared knowledge repository
  (`surveys/<id>/knowledge_repo/`), picked up automatically for every
  agent in that survey, no per-agent flag, matching how shared reference
  material works for a human panel; (3) a real web search if `"web_search"`
  is in the agent's `tools` list. A web search failure degrades to no
  results (logged via `storage.write_tool_call`, same mechanism RAG
  retrieval already used) rather than failing the agent: an optional
  grounding tool being briefly unavailable shouldn't block an otherwise
  answerable survey.
- New `web/backend/routers/knowledge.py`:
  `GET/POST /api/surveys/{id}/knowledge` (list/upload) and
  `DELETE .../knowledge/{filename}`. `.md`/`.txt` stored as-is; `.pdf`/
  `.docx` converted to plain text at upload time via the same full-text
  extraction the survey-criteria document parser uses internally (its
  *public* `parse_pdf`/`parse_docx` only keep lines matching a narrow
  "CODE: Label" heuristic, which would silently discard almost all of a
  real prose document; caught this before it shipped, not after).
- New **Knowledge** tab on the survey detail page (upload/list/delete), a
  **Web search** section on Settings (Tavily key, alongside the existing
  hosted-LLM-provider keys but visually separate since Tavily is a search
  API, not a selectable agent provider), and a `web_search` tools checkbox
  on the Agent form (previously `tools: []` had no UI control at all).
- `tests/test_web_search.py` (5), `tests/test_agent_tools.py` (6): 11 new
  tests covering the Tavily client, the shared-knowledge auto-pickup, the
  web_search tool only firing when granted, and graceful degradation on
  failure (with the failure itself logged). 78/78 tests pass repo-wide.
- **Live-verified with a real Ollama call, not just mocked tests**: created
  a throwaway survey, uploaded a knowledge file containing a fictional,
  invented-for-this-test marker phrase that exists nowhere else, ran a
  real agent against it, and confirmed that exact phrase appears in the
  real outgoing `prompt.md` sent to mistral:7b, labelled
  `[shared knowledge: kb_marker.md]`, proof the retrieval is real, not
  simulated. Test survey deleted afterward.

## 2026-08-03 (anti-hallucination: real, live model lists for every provider)

- New `web/backend/model_catalog.py`: `list_models(provider)` fetches the
  actual, live model list directly from that provider: Ollama's own
  `/api/tags`, or each hosted provider's own list-models API (OpenAI,
  OpenRouter, Groq, and Gemini via its OpenAI-compat endpoint all expose
  `GET {base}/models`; Anthropic has its own `GET /v1/models` with an
  `x-api-key` header). Never a hardcoded list, never trusting an LLM's
  guess. Degrades to `{"models": [], "error": "..."}` rather than raising
  when a provider is unreachable or has no API key configured, so callers
  (a UI dropdown, a validation check) can show *why* instead of crashing.
  `model_is_available(provider, model)` gives the benefit of the doubt
  (returns `True`) when the catalog itself couldn't be fetched, since
  absence of evidence isn't evidence of a hallucination.
- `GET /api/models/{provider}` replaces the Ollama-only
  `GET /api/ollama-models`; every model picker in the UI (the Agent
  form, the natural-language proposer's model picker) now re-fetches the
  real list every time the selected provider changes, for every provider,
  not just Ollama. Falls back to a free-text field with a visible warning
  when the list can't be fetched (no key configured, unreachable).
- `agent_proposer._annotate_model_availability` (added last session for
  Ollama-only) now checks every provider's "new" proposal against
  `model_catalog.model_is_available`, skipping `provider: manual` entries
  (no API list exists for those by definition). This is the fix Dan asked
  for directly after seeing the Ollama-only version catch a hallucinated
  model name: the same failure mode applies to every hosted provider,
  not just Ollama.
- `tests/test_model_catalog.py`: 9 new tests (one per provider's request
  shape, missing-key handling, manual/unknown-provider handling,
  unreachable-host degradation, benefit-of-the-doubt behaviour).
  `tests/test_agent_proposer.py`'s two Ollama-only availability tests
  rewritten against the generalized implementation. 67/67 tests pass.
- Live-verified: `GET /api/models/{provider}` for all 8 providers on the
  real deployment (Ollama returns its 9 real pulled models; every
  hosted provider correctly reports its missing API key rather than
  crashing); a real browser screenshot shows the Agent form's model field
  switching from a real Ollama dropdown to a free-text field with the
  "ANTHROPIC_API_KEY is not set" warning the moment the provider is
  changed to Anthropic.

## 2026-08-03 (rename executed, again: survey-agent-generation-engine -> Symphysis)

- GitHub repo renamed a third time, same day: `sage-khan/survey-agent-generation-engine`
  -> `sage-khan/symphysis-ai-research-survey-engine` (final name; GitHub
  redirects all three prior URLs: `agentic-survey-tool`, `sage`,
  `survey-agent-generation-engine`).
- veritas server checkout moved to
  `/home/veritas/projects/symphysis-ai-research-survey-engine`; backend
  container recreated with the updated mount, Vite frontend restarted from
  the new path. Same container name (`sage-backend`), ports, env vars.
- UI/branding updated throughout: sidebar now reads "Symphysis / AI
  Research Survey Engine" (was "SAGE / Survey Agent Generation Engine"),
  browser tab title, FastAPI app title ("Symphysis API"), README title,
  `.claude/rules/project-details.md` header, and the `agentic_survey`
  package docstring. New Agent Cards now record
  `environment.runtime: "symphysis"` (was `"sage"`); existing cards keep
  whatever value they were created with, as an accurate historical record.
  Verified: 57/57 tests pass, health checks green, browser screenshot
  confirms the new branding with zero console errors.

## 2026-08-03 (natural-language agent orchestrator)

- New `web/backend/agent_proposer.py` + `routers/proposer.py`:
  `POST /api/surveys/{id}/propose-agents` takes a plain-language requirement
  and calls an LLM (any configured provider) to propose a panel: each
  entry either `{"source": "library", "agent_id": ...}` (reuse an existing
  Agent Library entry) or `{"source": "new", ...}` (a fully-specified new
  agent). Nothing is written to disk by this call; it only returns the
  proposal for review. `POST /api/surveys/{id}/approve-agents` takes the
  (possibly user-edited) proposal list back and materializes it: "new"
  entries are created in the Agent Library first (so they're reusable
  going forward, not one-off) and then assigned into the survey; "library"
  entries are assigned directly. Each entry is handled independently and
  reports its own status: one bad entry doesn't block the rest.
- **Real finding from live testing, fixed same session**: the orchestrator
  LLM (qwen2.5:14b, phi4:14b, and others tried) reliably hallucinates
  plausible-sounding but non-existent Ollama model names for new agents
  (observed: "code-davinci", "legal-expert", "llama-2-7b-chat", none
  ever pulled on the test host). `parse_proposals`'s schema validation
  didn't catch this (it's a syntactically valid model name, just not an
  available one). Added `_annotate_model_availability`: every "new"
  ollama-provider proposal is checked against the live `/api/tags` model
  list and flagged `model_available: false` if not found, so the review
  UI can warn a human before approval rather than the agent silently
  failing only once the survey is actually run. Degrades safely if the
  Ollama host can't be reached (doesn't false-flag everything). This is
  advisory, not a hard block: approving an unfixed flagged entry is
  still possible (matches the general design: a human reviews and decides,
  nothing is auto-corrected on their behalf); confirmed live that both
  paths work (fixing the model before approving, and knowingly approving
  with the warning still showing).
- New "Describe what you need" panel on the survey Agents tab: requirement
  textarea, orchestrator provider/model picker, an editable review table
  (remove rows, edit display name/role/model, see the availability
  warning), and Approve.
- `tests/test_agent_proposer.py`: 10 new pure-function tests covering JSON
  extraction, all the validation-rejection paths (missing fields, unknown
  library id, duplicate/colliding new ids, invalid source), and the
  hallucinated-model-flagging behaviour (mocked, deterministic). 57/57
  tests pass repo-wide.
- Live-verified beyond the tests: a real qwen2.5:14b call proposing a real
  new agent for an actual live survey, a real phi4:14b call reproducing
  the hallucinated-model warning end-to-end in the browser, and a full
  propose -> edit -> approve -> materialized-in-library-and-survey pass
  with matching DIDs. All test agents created during verification were
  deleted afterward; the real survey/library end up unchanged.

## 2026-08-03 (Agent Library: reusable agents across surveys)

- New `agents_library/` (sibling to `surveys/`): Agent Cards that aren't
  tied to any one survey. `web/backend/routers/library.py` provides full
  CRUD (`GET/POST /api/library/agents`, `GET/PUT/DELETE
  /api/library/agents/{id}`) plus `POST /api/library/agents/{id}/assign/{survey_id}`,
  which copies (materializes) the library card into that survey's own
  `agents/` directory, keeping the same `agent_id` and `did:key` identity, so the
  existing orchestrator/storage/run pipeline (which only ever reads
  `surveys/<id>/agents/*.json`) needed no changes at all. Reuses
  `agents.py`'s `AgentIn` Pydantic schema and helpers rather than
  duplicating it; library and survey-scoped agents are the exact same
  Agent Card shape, just rooted in a different directory.
- New **Agent Library** page (sidebar nav, between Surveys and Settings):
  lists every reusable agent (ID, display name, role/expertise,
  provider/model, RAG, tools, DID) with create/edit/delete, reusing
  `AgentForm` in a new `scope="library"` mode.
- Survey detail page's Agents tab gained a **"+ Add from library"** picker
  alongside "+ Add agent": pick any library agent and assign it into the
  current survey with one click.
- `tests/test_web_library.py`: the first FastAPI `TestClient`-based test in
  this repo (httpx is already a transitive dependency), covering create,
  list, duplicate-create rejection, assign, duplicate-assign rejection,
  404s for a missing agent/survey, delete, and that deleting the library
  original leaves an already-assigned survey copy untouched. 47/47 tests
  pass.
- Live-verified beyond the test: created a real library agent via the API,
  assigned it into the live `trustrouter-agent-panel-live-20260803`
  survey, confirmed the identical DID appeared in that survey's agent
  list, confirmed the duplicate-assign 409, and confirmed the picker
  renders correctly on the actual running page (screenshot).

## 2026-08-03 (rename executed: sage -> survey-agent-generation-engine)

- GitHub repo renamed again, same day: `sage-khan/sage` ->
  `sage-khan/survey-agent-generation-engine` (the full descriptive name,
  not the short acronym, as the project's canonical identity; "SAGE"
  stays the UI's display name/acronym). GitHub redirects both the original
  `agentic-survey-tool` URL and the intermediate `sage` URL.
- veritas server: checkout moved `/home/veritas/projects/sage` ->
  `/home/veritas/projects/survey-agent-generation-engine`; backend
  container recreated with the updated volume mount; Vite frontend
  restarted from the new path. Same container name (`sage-backend`), same
  ports/env vars. Verified: 46/46 tests pass, health checks green, browser
  screenshot shows SAGE branding with zero console errors.
- Fixed the two remaining literal `sage` path references from the previous
  rename pass (README's repository-structure tree root and Docker volume
  mount example; `project-details.md`'s Repository line).

## 2026-08-03 (de-hardcoded config: one source of truth, adjustable in UI or by editing a file)

- New `config/defaults.yaml` (versioned baseline) + `agentic_survey/app_config.py`
  (`get_config()`/`save_overrides()`): the single source of truth for
  provider base URLs, default model/sampling/RAG hyperparameters for new
  agents, and the guardrail denylist starting point. Previously these were
  hardcoded literals duplicated across `agent_card.py`'s dataclass
  defaults, `web/backend/routers/agents.py`'s Pydantic defaults, and
  `AgentForm.jsx`'s `blankForm()`: three copies that could (and did, for
  the denylist) drift out of sync.
- `GroqProvider`/`GeminiProvider`/`XaiProvider`/`OpenAIProvider`/
  `OpenRouterProvider` now read their base URL from config (overridable
  without a code change, e.g. to point at a proxy or a different API
  version), falling back to the previous hardcoded URL only if
  `app_config` itself can't be imported.
- New `GET/PUT /api/settings/config` and a "Config: defaults for new
  agents" section on the Settings page: every value above is editable from
  the UI (persisted to gitignored `web/backend/data/config_overrides.json`,
  deep-merged onto `defaults.yaml` at read time; that file is never
  written to at runtime) or by editing `config/defaults.yaml` directly.
  Verified live: changing the default temperature via the API and then
  creating a new agent with no `model.temperature` supplied picked up the
  new value immediately, no backend restart.
- CORS's two local-dev default origins also now come from
  `config/defaults.yaml`'s `cors.default_origins` rather than a literal in
  `main.py` (the deployment-time `CORS_EXTRA_ORIGINS` env var is unchanged;
  that's legitimately a per-deployment concern, not a versioned default).

## 2026-08-03 (rebrand executed: repo + folder renamed, veritas-server deployment moved)

- GitHub repo renamed `sage-khan/agentic-survey-tool` -> `sage-khan/sage`
  (`gh repo rename`; GitHub redirects the old URL). Local remote updated to
  match.
- veritas server: local checkout moved
  `/home/veritas/projects/agentic-survey-tool` -> `/home/veritas/projects/sage`;
  Docker backend container recreated as `sage-backend` (was
  `agentic-survey-backend`) with its volume mount updated to the new path;
  Vite frontend restarted from the new path. Same ports (8100 backend, 5180
  frontend), same `OLLAMA_BASE_URL`/`CORS_EXTRA_ORIGINS` env vars. Verified:
  46/46 tests pass from the new location, health checks green, full browser
  screenshot pass shows SAGE branding with zero console errors.
- Nothing else about the deployment changed. See this same date's earlier
  entries for the feature/UX work the rename followed.

## 2026-08-03 (self-introduction turn, editable per-agent prompts, generic multi-provider settings, survey rename/created-at)

- **Self-introduction turn** (`agent.py`'s new `Agent.introduce()`, called at
  the start of `Agent.run()` for every non-manual provider): before
  attempting the actual survey task, each agent is asked to state its own
  agent ID, display name, base model, the current date/time, the project
  it's working on, and its role, and to confirm it will attempt the task as
  an expert in that role. Logged as the literal first entry in
  `conversation.jsonl` (`storage.write_introduction`), so a reviewer can
  check the model's actual understanding of the assignment before reading
  any Best/Worst reasoning. Skipped for `provider: manual` agents (a human
  is already pasting every response by hand).
- **Reasoning tab overhaul**: `thoughts.md` now opens with a plain-language
  explanation of what a "Sample" is (an independent repeat of the *same*
  question, not a sequence of different questions) and how many total
  attempts vs. accepted samples there were, and surfaces a reasoning model's
  raw Ollama `message.thinking` field (chain-of-thought) alongside its
  submitted `reasoning` summary when the provider returns one
  (`guardrails.GuardedRun.accepted_raw` now tracks the exact raw completion
  behind each accepted sample so the two can be paired up;
  `storage._extract_thinking`).
- **Conversation Log tab rewritten**: an explanatory banner at the top, and
  each event kind (introduction / model completion / rejected / tool call)
  rendered readably instead of a raw JSON dump. A reasoning model's
  "thinking" is in a collapsible `<details>`, a rejected attempt shows its
  guardrail error(s) in red plus the raw text, etc.
- **Downloads added** to the Trace viewer: "Download agent card .json" and
  "Download full log .jsonl" buttons.
- **Editable per-agent system prompt**: `AgentCard.system_prompt_override`
  (new optional field) takes precedence over `system_prompt_template` when
  set; editable directly as free text in the web UI's agent form, no
  `{role}`/`{role_description}` substitution applied (avoids a crash if the
  user's own text happens to contain a stray `{`/`}`).
- **`display_name` and `expertise` fields** added to the Agent Card schema
  and the create/edit form and Agents-tab table, alongside the existing
  `role`/`role_description` (a short structured profession/expertise line,
  distinct from the longer narrative `role_description`).
- **Settings genericized**: the hardcoded "Veritas server (Tailscale)"
  preset is gone; "Local" is the only built-in Ollama preset now, and any
  remote endpoint can be saved under a label of the user's choosing
  (`PUT /api/settings/llm`'s new `save_preset_label`,
  `DELETE /api/settings/llm/presets/{label}`). Added a
  **Hosted-provider API keys** section (`GET/PUT /api/settings/api-keys`)
  covering Anthropic, OpenAI, OpenRouter, Groq, Gemini, and xAI (Grok).
  Keys are stored locally (gitignored `llm_settings.json`), applied to the
  process environment, and never echoed back once saved (only whether a key
  is set is shown). New provider classes `GroqProvider`, `GeminiProvider`
  (via Google's OpenAI-compatibility endpoint), `XaiProvider` in
  `providers/openai_compatible.py`, registered in `providers/__init__.py`.
- **Survey `created_at` and rename**: `create_survey` now stamps a real UTC
  timestamp; the Surveys list shows a Created column. A new
  `PATCH /api/surveys/{id}` endpoint (and a Rename button on the survey
  detail page) lets the display title be changed after creation. The
  survey `id` itself (the directory name every agent card's
  `permissions.data_scopes`/`rag.corpus_path` bakes in) stays immutable by
  design; see the endpoint's docstring for why. Also added an optional
  survey `description` (shown to agents in their introduction) and
  clarified the New Survey form's Code vs. Label columns, which were
  previously unlabelled jargon.

## 2026-08-03 (Analytics tab; server-deployment procedure documented in README)

- Added `GET /api/surveys/{id}/analytics` (`web/backend/analytics.py`,
  pure/FastAPI-free, unit-tested in `tests/test_web_analytics.py`) and a new
  Analytics tab on the survey detail page: a panel-participation summary
  (`contributed`/`zero_accepted`/`pending_manual`/`skipped`/`not_run`, each
  classified from what's actually on disk), a Best/Worst pick-frequency
  count per criterion, and a full "who said what" table (one row per
  accepted sample: agent, role, model, RAG, Best, Worst, reasoning) plus a
  non-contributing-agents table with the specific reason for each. Answers
  "which agent said what" and "who didn't respond, and why" directly,
  rather than requiring a click into every agent's Trace individually or
  inferring non-response from an agent's absence in the Results tab.
- README: added "Deploying on a shared server" (the exact Docker
  `--network host` backend + `nvm`-Node frontend + `CORS_EXTRA_ORIGINS`
  procedure used to run this app on the veritas server, where there's no
  system pip/venv and no passwordless sudo), and "Where everything lives"
  (UI URLs, project-folder layout, `.zip` download, trace files, report
  files); previously this was only ever explained ad hoc, not documented.

## 2026-08-03 (live 17-agent run against the real uploaded survey; RAG-permission bug fix)

- Deployed the web UI on the veritas server itself (not just accessed
  remotely from a local sandbox): FastAPI backend in a `python:3.11-slim`
  Docker container on `--network host` (so it reaches the host's Ollama at
  `localhost:11434` and is reachable over Tailscale on port 8100), React
  frontend via the server's `nvm`-installed Node on port 5180.
- `web/backend/main.py`: CORS origins are now `CORS_EXTRA_ORIGINS`
  (comma-separated env var) appended to the existing localhost defaults,
  so the UI can be reached at the server's Tailscale IP without hardcoding
  it into source.
- Uploaded the real LimeSurvey export (`limesurvey_survey_185662.lss`, the
  actual TrustRoute human-panel survey, not a synthetic stand-in) through
  `/api/surveys/parse`, confirmed the parser's documented best-effort
  behaviour (it surfaces every question row as a raw candidate for human
  curation, exactly as designed, not a bug), then created a new survey
  (`trustrouter-agent-panel-live-20260803`) with the six real DVS
  dimensions (Q, PT, V, IC, L, C) and their real definition text, both
  read directly out of the uploaded `.lss` XML rather than retyped from
  memory.
- Created all 17 agents from the `bsi-hawc-bwm` example roster's design
  (6 domain-persona roles x base/RAG on 6 distinct Ollama model families,
  plus the 5-agent independent-reviewer tier) through the real
  `POST /api/surveys/{id}/agents` endpoint, not by copying JSON files, so
  every agent's DID was freshly and correctly derived for this survey.
- Ran the panel for real against the server's Ollama and (where
  credentialed) Anthropic. Found and fixed a real bug in the process: see
  `diagnostics.md`, "Every RAG-enabled agent was silently skipped."

## 2026-08-02 (README rewrite + documentation-maintenance rule)

- Rewrote `README.md`: added a "How it works" pipeline diagram (Agent Card
  -> Agent -> provider -> instrument -> guardrails -> storage -> solvers ->
  reporting), an annotated full "Repository structure" tree (previously
  only directories were listed, not the runtime-written files inside each
  agent's folder), and three "main files" reference tables (one each for
  `src/agentic_survey/`, `web/backend/`, `web/frontend/src/`) giving a
  one-line purpose for every source file in the repo. Reorganized Quick
  start + Web UI setup + Remote-LLM mode under one "Setup" section.
- Added `.claude/rules/documentation-maintenance.md`: a standing rule that
  any change to a file/endpoint/workflow described in `README.md` updates
  the relevant README section in the same change, and that any change
  worth a commit gets a `changelog.md` entry (with a `diagnostics.md`
  entry too, if it was a bug fix). Written after noticing this README had
  drifted: it described "Quick start" and "Web UI" as separate,
  loosely-connected sections with no full file-level reference, even
  though the repo had grown to 30+ source files across three languages.

## 2026-08-02 (LLM-endpoint settings)

- Added a runtime-configurable LLM endpoint: `GET/PUT /api/settings/llm` and
  a `GET /api/settings/llm/test` connectivity check, backed by
  `web/backend/routers/settings.py` and a new Settings page in the web UI.
  Previously switching between a local Ollama instance and the veritas
  server meant editing `.env`/`OLLAMA_BASE_URL` and restarting the backend
  process; now it's a preset button (Local / Veritas server (Tailscale) /
  Custom) plus Test connection and Save, persisted to
  `web/backend/data/llm_settings.json` (gitignored, machine-specific) and
  restored on the next backend start.
- `agentic_survey.providers.reset_provider()`: the provider registry cached
  the `ollama` provider instance (and its `base_url`) for the life of the
  process, so a long-lived web backend could never actually pick up a
  changed `OLLAMA_BASE_URL` after the first run. The settings endpoint now
  clears the cache after writing the new value so the very next survey run
  uses it.
- Verified end to end against the real veritas server over Tailscale (not
  mocked): saved the veritas-server preset, ran a live single-agent
  `mistral:7b` survey through it from this endpoint, confirmed the run
  completed, and confirmed the resulting chart rendered correctly in the
  browser. See `diagnostics.md` for a real chart-rendering bug this same
  run surfaced.

## 2026-08-02 (web UI)

- Web UI MVP: FastAPI backend (`web/backend/`) + React/Vite frontend
  (`web/frontend/`), kept as a separate layer on top of `agentic_survey`
  since this UI is intended to grow into its own product. Survey
  create/list/delete, document-upload parsing into candidate criteria
  (structured Markdown, LimeSurvey `.lss`, best-effort PDF/DOCX), Agent
  Card create/edit/delete through a form, background survey runs with
  status polling, results view (weight tables, charts, rendered report),
  per-agent trace viewer (filled survey, reasoning, exact prompt, parsed
  conversation log), `.zip` download.
- Verified end to end in a real headless-Chromium browser (Playwright),
  not just via curl: the full create-survey -> add-agent -> run ->
  paste-manual-response -> re-run -> view-results loop, including the
  exact "re-run after pasting, same long-lived server process" scenario
  that surfaced the sample-index bug described in `diagnostics.md`.
- Fixed during that verification: the manual provider's sample-index
  tracking (a module-level counter assumed the process restarts between
  runs, which is true for the CLI but not for the web backend) and the
  run-status classification (a survey where every agent is legitimately
  awaiting a manual paste was reported as `error` instead of a distinct
  `pending_manual` status). See `diagnostics.md` for both.
- Confirmed real, remote LLM calls flow correctly through the whole stack
  by exercising the existing `bsi-hawc-bwm` example survey's live 17-agent
  roster through the new `/api/surveys/{id}/agents` endpoint.

## 2026-08-02

- Full trace and consolidated output per agent: every provider's exact
  outgoing prompt is now logged (`prompt.md`), RAG retrieval is logged as a
  discrete tool-call event in `conversation.jsonl`, and each agent gets a
  single human-readable `filled_survey.md` (role/model/DID/RAG header,
  Best/Worst summary table, full comparison tables and reasoning per
  sample) instead of needing `samples/*.json` and `conversation.jsonl` open
  side by side.
- Confirmed remote-LLM mode: the app can run entirely on a local machine
  while calling the veritas server's Ollama instance over Tailscale
  (`OLLAMA_BASE_URL=http://<tailscale-ip>:11434`); the Bayesian solve stays
  local and fast regardless of where the LLM calls go.
- Copied and curated VERITAS's project-wide `.claude/rules/` into this repo
  (gitops, file-read-write, software-directory-structure-guide,
  writing-style, aboutme), dropping the paper/literature-specific rules
  that don't apply to a software tool repo, and wrote this project's own
  `project-details.md`.

## 2026-08-02 (earlier)

- Agent Card redesign: agents are now spawned from a single portable JSON
  file (DID, role, model, RAG, sampling, permissions, guardrails,
  environment) instead of split YAML config + a runtime-generated DID.
  Real `did:key` identity (Ed25519, W3C Verifiable Credentials), ported from
  project-cogtwins's verified `identity.py` pattern.
- Added a `manual` provider for models with no API (Gemini/GPT web chat):
  writes the exact prompt to paste, waits for the pasted reply, resumes
  across process restarts without re-asking answered samples.
- Permissions (`data_scopes`, `allowed_providers`) enforced, not just
  documented.
- Migrated the example `bsi-hawc-bwm` survey's roster to 17 agents: 6
  domain-persona roles (BIM coordinator, compliance officer, structural
  engineer, project manager, blockchain engineer, data engineer) each bound
  to one of 6 diverse Ollama model families (Qwen, Gemma, Llama, Mistral,
  DeepSeek, Phi), plus a 5-agent "independent reviewer" cross-check tier
  (Claude Opus/Sonnet/Haiku, manual Gemini/GPT).
- Live end-to-end validation on the veritas server (real LLM calls, not
  mocked) surfaced and fixed three real bugs; see `diagnostics.md`.

## 2026-08-01

- Initial release: config-driven agents (YAML at this point), provider
  abstraction (Ollama/Anthropic/OpenAI/OpenRouter), BWM instrument,
  guardrails (schema validation, retry, repeated sampling), classical and
  Bayesian BWM solvers ported from `bsi-survey-app` and verified against the
  original authors' reference implementations, Docker deployment, initial
  `bsi-hawc-bwm` example survey.
