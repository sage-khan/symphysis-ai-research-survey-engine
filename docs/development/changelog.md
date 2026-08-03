# Changelog

All notable changes to SAGE (formerly agentic-survey-tool). Bug fixes and their root causes
are tracked separately in `diagnostics.md`.

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
