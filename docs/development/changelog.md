# Changelog

All notable changes to agentic-survey-tool. Bug fixes and their root causes
are tracked separately in `diagnostics.md`.

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
