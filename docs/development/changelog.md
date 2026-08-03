# Changelog

All notable changes to Symphysis (formerly SAGE, formerly agentic-survey-tool). Bug fixes and their root causes
are tracked separately in `diagnostics.md`.

## 2026-08-03 (anti-hallucination: real, live model lists for every provider)

- New `web/backend/model_catalog.py`: `list_models(provider)` fetches the
  actual, live model list directly from that provider -- Ollama's own
  `/api/tags`, or each hosted provider's own list-models API (OpenAI,
  OpenRouter, Groq, and Gemini via its OpenAI-compat endpoint all expose
  `GET {base}/models`; Anthropic has its own `GET /v1/models` with an
  `x-api-key` header). Never a hardcoded list, never trusting an LLM's
  guess. Degrades to `{"models": [], "error": "..."}` rather than raising
  when a provider is unreachable or has no API key configured, so callers
  (a UI dropdown, a validation check) can show *why* instead of crashing.
  `model_is_available(provider, model)` gives the benefit of the doubt
  (returns `True`) when the catalog itself couldn't be fetched -- absence
  of evidence isn't evidence of a hallucination.
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
  model name -- the same failure mode applies to every hosted provider,
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
  redirects all three prior URLs -- `agentic-survey-tool`, `sage`,
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
  and calls an LLM (any configured provider) to propose a panel -- each
  entry either `{"source": "library", "agent_id": ...}` (reuse an existing
  Agent Library entry) or `{"source": "new", ...}` (a fully-specified new
  agent). Nothing is written to disk by this call; it only returns the
  proposal for review. `POST /api/surveys/{id}/approve-agents` takes the
  (possibly user-edited) proposal list back and materializes it: "new"
  entries are created in the Agent Library first (so they're reusable
  going forward, not one-off) and then assigned into the survey; "library"
  entries are assigned directly. Each entry is handled independently and
  reports its own status -- one bad entry doesn't block the rest.
- **Real finding from live testing, fixed same session**: the orchestrator
  LLM (qwen2.5:14b, phi4:14b, and others tried) reliably hallucinates
  plausible-sounding but non-existent Ollama model names for new agents
  (observed: "code-davinci", "legal-expert", "llama-2-7b-chat" -- none
  ever pulled on the test host). `parse_proposals`'s schema validation
  didn't catch this (it's a syntactically valid model name, just not an
  available one). Added `_annotate_model_availability`: every "new"
  ollama-provider proposal is checked against the live `/api/tags` model
  list and flagged `model_available: false` if not found, so the review
  UI can warn a human before approval rather than the agent silently
  failing only once the survey is actually run. Degrades safely if the
  Ollama host can't be reached (doesn't false-flag everything). This is
  advisory, not a hard block -- approving an unfixed flagged entry is
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
  `agents/` directory -- same `agent_id`, same `did:key` identity -- so the
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
  not the short acronym, as the project's canonical identity -- "SAGE"
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
  `AgentForm.jsx`'s `blankForm()` -- three copies that could (and did, for
  the denylist) drift out of sync.
- `GroqProvider`/`GeminiProvider`/`XaiProvider`/`OpenAIProvider`/
  `OpenRouterProvider` now read their base URL from config (overridable
  without a code change, e.g. to point at a proxy or a different API
  version), falling back to the previous hardcoded URL only if
  `app_config` itself can't be imported.
- New `GET/PUT /api/settings/config` and a "Config -- defaults for new
  agents" section on the Settings page: every value above is editable from
  the UI (persisted to gitignored `web/backend/data/config_overrides.json`,
  deep-merged onto `defaults.yaml` at read time -- that file is never
  written to at runtime) or by editing `config/defaults.yaml` directly.
  Verified live: changing the default temperature via the API and then
  creating a new agent with no `model.temperature` supplied picked up the
  new value immediately, no backend restart.
- CORS's two local-dev default origins also now come from
  `config/defaults.yaml`'s `cors.default_origins` rather than a literal in
  `main.py` (the deployment-time `CORS_EXTRA_ORIGINS` env var is unchanged
  -- that's legitimately a per-deployment concern, not a versioned default).

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
- Nothing else about the deployment changed -- see this same date's earlier
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
  rendered readably instead of a raw JSON dump -- a reasoning model's
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
  covering Anthropic, OpenAI, OpenRouter, Groq, Gemini, and xAI (Grok) --
  keys are stored locally (gitignored `llm_settings.json`), applied to the
  process environment, and never echoed back once saved (only whether a key
  is set is shown). New provider classes `GroqProvider`, `GeminiProvider`
  (via Google's OpenAI-compatibility endpoint), `XaiProvider` in
  `providers/openai_compatible.py`, registered in `providers/__init__.py`.
- **Survey `created_at` and rename**: `create_survey` now stamps a real UTC
  timestamp; the Surveys list shows a Created column. A new
  `PATCH /api/surveys/{id}` endpoint (and a Rename button on the survey
  detail page) lets the display title be changed after creation -- the
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
  files) -- previously this was only ever explained ad hoc, not documented.

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
  drifted -- it described "Quick start" and "Web UI" as separate,
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
