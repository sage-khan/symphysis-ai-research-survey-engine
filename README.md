# Symphysis: AI Research Survey Engine

Config-driven, replicable agent panels for expert-elicitation surveys.
Formerly named `agentic-survey-tool` (that's still the internal Python
package name, `agentic_survey`, and how earlier session records refer to
it); renamed to SAGE, then to Symphysis, as it moves toward being a standalone product rather
than a component scoped to one paper. Built as the general-purpose
successor to VERITAS's `bsi-survey-app`, starting from the BSI paper's
HAWC-BWM (Human-AI Weighted Consensus Best-Worst Method) use case, but
designed so a survey can plug in a different instrument (AHP, etc.) without
touching the agent, provider, or storage layers.

## What it does

1. **Spawns agents from a portable Agent Card.** Every agent is fully
   defined by one JSON file (`surveys/<id>/agents/<agent-id>.json`): a real
   `did:key` identity, role, model + hyperparameters, RAG corpus (if any),
   sampling policy, tools, permissions (which data paths and providers it
   may use), and guardrails (denylist patterns). Give someone this file
   (plus the shared DID seed, for a reproducible identity) and they can
   respawn an identical agent anywhere, without reading this app's source.
   See "The Agent Card" below.
2. **Runs an instrument against each agent.** The instrument owns the prompt
   construction and response schema; agents don't know or care which
   instrument they're completing. `bwm` (Best-Worst Method) is implemented;
   the interface (`src/agentic_survey/instruments/base.py`) is designed for
   AHP and others to be added the same way.
3. **Enforces permissions, not just documents them.** A RAG-enabled agent's
   `corpus_path` must match one of its card's `permissions.data_scopes`
   globs or the agent refuses to start; its provider must be in
   `permissions.allowed_providers`. See `permissions.py`.
4. **Applies guardrails.** Every response is schema-validated and
   rejected/re-sampled on malformed output; a denylist regex scan catches
   prompt-injection markers or secret-shaped strings even in otherwise
   well-formed output; every agent is sampled multiple times (never a
   single completion treated as ground truth); every raw model completion
   (not just the parsed answer) is logged for audit.
5. **Supports models with no API.** A `provider: manual` agent (e.g. the
   Gemini or GPT web chat UI, which Dan has no API key for) writes out the
   exact prompt to paste into that chat, waits for the pasted-back reply,
   and resumes exactly where it left off on the next run. See "Manual
   paste-in agents" below.
6. **Solves and combines.** The classical BWM linear program (Rezaei, 2015)
   and the Bayesian hierarchical BWM (Mohammadi and Rezaei, 2020) are ported
   from `bsi-survey-app`, verified against the original author's reference
   JAGS implementation (github.com/Majeed7/BayesianBWM), and one real bug
   fixed in the process (see `docs/development/diagnostics.md`). A parallel
   human-panel posterior can be combined with the agent-panel posterior via
   a draw-wise linear pool across a full alpha sensitivity sweep (HAWC-BWM).
7. **Persists everything per survey, per agent.** See "Repository structure"
   below.
8. **Reports.** Markdown report plus matplotlib PNG charts (posterior
   weights with credible intervals, HAWC-BWM sensitivity sweep), viewable
   both as files on disk and embedded in the web UI's results page.
9. **Analytics: who said what.** A dedicated Analytics tab (and
   `GET /api/surveys/{id}/analytics`) answers "which agent said what, and
   who didn't respond at all" directly: a per-sample table of every
   accepted Best/Worst pick and its reasoning, a Best/Worst pick-frequency
   count per criterion, and an honest per-agent participation breakdown
   (`contributed` / `zero_accepted` / `pending_manual` / `skipped` /
   `not_run`, each with why). See "Analytics: who said what" below.

## How it works (request/response pipeline)

One agent's run through `orchestrator.run_survey` (`src/agentic_survey/orchestrator.py`):

```
Agent Card (JSON)                survey.yaml
   |                                 |
   v                                 v
agent_card.load_card()  ----->  Agent(card, storage)          [agent.py]
   |                                 |
   |                     permissions.check_provider_allowed / check_data_scope
   |                                 |
   |                     rag.retriever.build_retriever()  (only if card.rag.enabled)
   |                                 |
   v                                 v
instrument.build_messages()  -->  providers.get_provider(card.model.provider).complete()
   |                                 |
   v                                 v
guardrails.run_with_guardrails()  (schema validation, denylist scan, repeated
   |                                 sampling, reject-and-resample on malformed output)
   v
storage.write_*()  (prompt.md, conversation.jsonl, thoughts.md, samples/, filled_survey.md, result.json)
   |
   v  (once every agent in the survey has run)
solvers.bwm_classical / bwm_bayesian.solve()  -->  reporting.render_report() + render_charts()
```

If the survey config sets `weighting.human_responses_path`, the agent-panel
posterior is combined with a human-panel posterior
(`bwm_bayesian.combine_panels`, the HAWC-BWM draw-wise linear pool across an
alpha sensitivity sweep) before reporting.

The web UI (`web/backend/`, `web/frontend/`) is a thin HTTP layer on top of
this same pipeline: it does not reimplement any of it, it calls
`load_survey_config` + `run_survey` in a background thread
(`web/backend/runs.py`) and serves the same on-disk artifacts (report,
charts, per-agent trace files) as JSON/file responses.

## Repository structure

```
symphysis-ai-research-survey-engine/
├── src/agentic_survey/          # the core package: see table below (import name kept stable)
├── config/
│   └── prompts/                 # shared system-prompt templates (referenced by agent cards)
├── surveys/<survey-id>/         # one directory per survey project
│   ├── survey.yaml              # instrument, dimensions, HAWC-BWM weighting/sweep config
│   ├── agents/<agent-id>.json   # the portable Agent Card (source config, see "The Agent Card")
│   ├── rag_corpora/<role>/      # disclosed, held-out RAG corpus per role (SOURCES.md inside)
│   ├── human_responses/         # per-expert JSON export (e.g. LimeSurvey), for HAWC-BWM combination
│   ├── agents/<agent-id>/       # written at runtime, one folder per agent:
│   │   ├── card.json            #   copy of the card actually used for this run
│   │   ├── did.json             #   this agent's did:key + public key (from the card)
│   │   ├── prompt.md            #   the exact outgoing prompt, every provider
│   │   ├── manual_input/        #   provider: manual agents only, prompt_NN.md / response_NN.txt
│   │   ├── conversation.jsonl   #   every raw completion, rejection, and tool call (RAG retrieval)
│   │   ├── thoughts.md          #   human-readable reasoning trace
│   │   ├── samples/             #   sample_NN.{json,md}, each accepted schema-valid response
│   │   ├── filled_survey.md     #   consolidated, human-readable completed survey for this agent
│   │   └── result.json          #   this agent's accepted payloads + guardrail summary
│   └── report/                  # written at runtime, once per survey run:
│       ├── report.md            #   the full markdown report
│       ├── combined_results.json
│       └── charts/*.png         #   PNG charts (also served by the web UI, see below)
├── web/
│   ├── backend/                 # FastAPI app: see table below
│   │   └── data/                #   gitignored: llm_settings.json (machine-specific runtime state)
│   └── frontend/                # React/Vite app: see table below
├── docker/Dockerfile
├── docker-compose.yml
├── requirements.txt              # core package deps
├── pytest.ini
├── .env.example                  # documents every env var this app reads
├── docs/development/
│   ├── changelog.md              # what changed and when (see "Keeping this README/changelog current")
│   └── diagnostics.md            # bugs found, root cause, and fix
├── .claude/rules/                 # AI-agent working rules for this repo (see "Documentation" below)
└── tests/                         # pytest, mirrors src/agentic_survey's layout
```

### Core package (`src/agentic_survey/`): what each file does

| File | Purpose |
|---|---|
| `cli.py` | Command-line entrypoint: `python -m agentic_survey.cli run <survey-dir>`. |
| `config.py` | Loads and validates `survey.yaml` into a `SurveyConfig` (instrument, dimensions, weighting, discovered agent cards). |
| `agent_card.py` | The portable Agent Card: one JSON file that fully defines a spawnable agent (model, RAG, sampling, permissions, guardrails, did). `new_card()` / `load_card()`. |
| `did_key.py` | Real `did:key` identity + W3C-shaped Verifiable Credentials (Ed25519), ported from project-cogtwins's `identity.py`. |
| `agent.py` | One agent instance: resolves its role prompt, builds RAG context if enabled, calls its provider through the guardrails layer, and persists everything via `storage`. |
| `permissions.py` | Enforces (not just documents) an Agent Card's `data_scopes` and `allowed_providers` before any file is read or provider called. |
| `guardrails.py` | Schema validation + reject-and-resample, denylist regex scan (prompt-injection / secret-shaped strings), repeated sampling, applied to every provider call. |
| `orchestrator.py` | Drives one full survey run: spawn every agent, run the instrument, solve the agent-panel posterior, optionally combine with a human panel (HAWC-BWM), write the report. `INSTRUMENTS` registry lives here. |
| `storage.py` | The per-survey / per-agent runtime folder layout (see "Repository structure" above): every `write_*` call the rest of the package makes. |
| `reporting.py` | Renders `report.md` and the matplotlib PNG charts (`render_report`, `render_charts`) from a survey's combined result dict. |
| `providers/` | One `LLMProvider` implementation per backend: `ollama_provider.py` (local/remote Ollama HTTP API, reads `OLLAMA_BASE_URL`), `anthropic_provider.py`, `openai_compatible.py` (OpenAI + OpenRouter), `manual_provider.py` (paste-in models with no API), `base.py` (the `LLMProvider` protocol). `__init__.py` is the provider registry (`get_provider`, `reset_provider`). |
| `instruments/` | `base.py` is the `Instrument` protocol (`build_messages` + `parse`); `bwm.py` is the Best-Worst Method instrument (prompt construction + response schema). |
| `solvers/` | `bwm_classical.py` (Rezaei 2015 linear program + consistency ratio), `bwm_bayesian.py` (Mohammadi & Rezaei 2020 hierarchical Bayesian model, PyMC/NUTS with a numpy-bootstrap fallback, plus `combine_panels` for HAWC-BWM). |
| `rag/retriever.py` | Minimal pluggable RAG: chunks every `.txt`/`.md` file under a corpus directory, retrieves top-k via sentence-transformers cosine similarity or falls back to dependency-free TF-IDF. |

### Web backend (`web/backend/`): what each file does

| File | Purpose |
|---|---|
| `main.py` | FastAPI app entrypoint; wires up CORS, includes every router, restores persisted LLM settings on startup. |
| `paths.py` | Resolves `REPO_ROOT`/`SRC_DIR`/`SURVEYS_ROOT` regardless of the process's working directory; puts `src/` on `sys.path`. |
| `runs.py` | In-process background-run tracker (a dict + a daemon thread per run): runs a survey without blocking the request/response cycle. |
| `routers/surveys.py` | Survey CRUD, document-upload parsing, run/run-status, results, analytics, chart file serving, `.zip` download. |
| `routers/agents.py` | Agent Card CRUD through the web form, full per-agent trace endpoint, `/api/providers` and `/api/ollama-models`. |
| `routers/settings.py` | LLM-endpoint settings (`GET/PUT /api/settings/llm`, `GET /api/settings/llm/test`); see "Remote-LLM mode" below. |
| `analytics.py` | Pure, FastAPI-free aggregation used by `GET /api/surveys/{id}/analytics`: classifies every configured agent (`contributed`/`zero_accepted`/`pending_manual`/`skipped`/`not_run`) from what's actually on disk, and tallies Best/Worst pick frequency per criterion. See "Analytics: who said what" below. |
| `parsing/markdown_parser.py` | Parses a structured Markdown survey definition into candidate dimensions. |
| `parsing/lss_parser.py` | Best-effort LimeSurvey `.lss` (XML) parser; surfaces every question row as a candidate dimension. |
| `parsing/document_parser.py` | Best-effort PDF/DOCX candidate-dimension extraction (text-pattern heuristic, not structural). |

### Web frontend (`web/frontend/src/`): what each file does

| File | Purpose |
|---|---|
| `App.jsx` | Top-level layout: sidebar nav (Surveys / Settings) and page routing. |
| `api.js` | The only place that calls the backend: one `fetch`-based function per endpoint. |
| `pages/SurveysPage.jsx` | Survey list + "New survey" panel (upload a document or enter criteria manually). |
| `pages/SurveyDetailPage.jsx` | One survey's three tabs: Agents (list/add/edit/delete + per-agent trace), Results (weight tables, charts, rendered report, `.zip` download), and Analytics (panel-participation summary, Best/Worst frequency, the full "who said what" sample table, and a non-contributing-agents table with the reason for each). |
| `pages/SettingsPage.jsx` | The LLM-endpoint settings page (presets, custom URL, test connection, save); see "Remote-LLM mode" below. |
| `components/AgentForm.jsx` | The create/edit form for one Agent Card. |
| `components/TraceViewer.jsx` | Tabbed viewer for one agent's filled survey / reasoning / prompt / raw conversation log. |
| `components/StatusDot.jsx` | The small colored status indicator (`idle`/`running`/`complete`/`error`/`pending_manual`). |

## Setup

```bash
pip install -r requirements.txt

export ANTHROPIC_API_KEY=...   # only needed for agents configured with provider: anthropic
export OPENAI_API_KEY=...      # only needed for agents configured with provider: openai
export OPENROUTER_API_KEY=...  # only needed for agents configured with provider: openrouter
export OLLAMA_BASE_URL=...     # defaults to http://localhost:11434

PYTHONPATH=src python -m agentic_survey.cli run surveys/bsi-hawc-bwm
```

Or dockerized:

```bash
docker compose up --build
```

Output lands in `surveys/bsi-hawc-bwm/report/report.md` and `.../charts/`.

The example survey's agent roster spans 6 diverse Ollama model families
(Qwen, Gemma, Llama, Mistral, DeepSeek, Phi, one per domain-persona role,
so base-vs-RAG comparisons hold the model constant within a role) plus a
5-agent "independent reviewer" cross-check tier (Claude Opus/Sonnet/Haiku
via the Anthropic API, and manually-pasted Gemini/GPT).

### Web UI setup

A FastAPI backend (`web/backend/`) and React/Vite frontend (`web/frontend/`)
sit on top of the same `agentic_survey` package, deliberately kept as a
separate layer since this UI is intended to grow into its own product.

```bash
# Backend (from the repo root)
pip install -r web/backend/requirements.txt
PYTHONPATH=web uvicorn backend.main:app --reload --port 8000

# Frontend (separate terminal)
cd web/frontend
npm install
npm run dev   # http://localhost:5173
```

The UI lets you: upload a survey document (structured Markdown, LimeSurvey
`.lss`, or best-effort PDF/DOCX) and review its parsed candidate criteria
before creating a survey; create, edit, and delete Agent Cards through a
form (role, model/provider, hyperparameters, RAG corpus, guardrails); pick
which Ollama endpoint agents call (Settings page, see below); run a survey
and watch its status (`idle` / `running` / `awaiting paste` / `complete` /
`error`); view each agent's full trace (filled survey, reasoning, exact
prompt, raw conversation log) plus the combined results and charts, with a
one-click `.zip` download of everything; and see the whole panel's Analytics
tab (who said what, and who didn't); see "Analytics: who said what" below.

## Deploying on a shared server (no local pip/venv, no passwordless sudo)

This is the procedure actually used to deploy and run this app on the
veritas server (Tailscale-reachable, no system `pip`/`venv` and no
passwordless `sudo` there, `docker` available). It differs from the local
"Web UI setup" above only in *how* the two processes get their
dependencies and get exposed on the network; the app itself is unchanged.

**Backend, in Docker on `--network host`** (so it reaches a local Ollama at
`localhost:11434` with no extra networking, and is reachable on the host's
own IP/Tailscale address on whatever port you publish):

```bash
docker run -d --name agentic-survey-backend \
  --network host \
  -v /path/to/symphysis-ai-research-survey-engine:/app \
  -w /app \
  -e OLLAMA_BASE_URL=http://localhost:11434 \
  -e PYTHONPATH=/app/web:/app/src \
  -e CORS_EXTRA_ORIGINS=http://<server-tailscale-ip>:5180 \
  python:3.11-slim \
  bash -c "apt-get update -qq && apt-get install -y --no-install-recommends -qq g++ >/dev/null \
    && pip install -q --no-cache-dir -r requirements.txt -r web/backend/requirements.txt \
    && exec uvicorn backend.main:app --host 0.0.0.0 --port 8100"
```

`CORS_EXTRA_ORIGINS` (comma-separated) is exactly for this case: the
frontend origin is the server's own Tailscale IP, not `localhost`, so it
needs to be explicitly allowed alongside the two local-dev defaults (see
`web/backend/main.py`). Pick a port other than 8100 if something else on
the host already listens there.

**Frontend, via whatever Node the server has** (a system Node install, or a
version manager like `nvm` if that's what's available: no Docker needed
for this side, it's just a static dev server):

```bash
cd web/frontend
echo "VITE_API_BASE=http://<server-tailscale-ip>:8100" > .env
npm install
nohup npm run dev -- --host 0.0.0.0 --port 5180 > /tmp/vite.log 2>&1 &
disown
```

**Verify both are actually reachable** (from any machine on the same
Tailscale network, not just `localhost` on the server):

```bash
curl http://<server-tailscale-ip>:8100/api/health   # {"status": "ok"}
curl -o /dev/null -w '%{http_code}\n' http://<server-tailscale-ip>:5180/   # 200
```

Then open `http://<server-tailscale-ip>:5180` in a browser on any device
that's on the same Tailscale network. Both processes are long-lived
(the Docker container restarts-on-demand; the Vite dev server keeps running
in the background via `nohup`/`disown`); no need to redeploy between
survey runs, only when the source changes (the backend needs a
`docker restart agentic-survey-backend` to pick up a code change since
Python doesn't hot-reload; the frontend picks up changes immediately via
Vite's HMR).

## Where everything lives

- **The UI**: `http://<server-tailscale-ip>:5180` (frontend) talking to
  `http://<server-tailscale-ip>:8100` (backend API); see "Deploying on a
  shared server" above for how those get started.
- **Every survey's project folder**: `surveys/<survey-id>/` in the repo
  checkout the backend was started from (see "Repository structure" above
  for the full layout: `survey.yaml`, `agents/<id>.json` configs,
  `rag_corpora/`, and, once run, each agent's `agents/<id>/` runtime folder
  plus the survey-level `report/` folder).
- **Fastest way to grab everything for one survey**: click "Download .zip"
  on that survey's page (or `GET /api/surveys/{id}/download`); it zips
  the entire `surveys/<survey-id>/` folder, configs and runtime output
  together.
- **One agent's full reasoning trace**: that agent's row's "Trace" button
  in the Agents tab (Filled Survey / Reasoning / Prompt / Conversation Log),
  or read the files directly:
  `surveys/<survey-id>/agents/<agent-id>/{filled_survey.md,thoughts.md,prompt.md,conversation.jsonl,result.json}`.
- **The combined weight-elicitation results**: the Results tab (weight
  table + posterior chart + full rendered report), or
  `surveys/<survey-id>/report/{report.md,combined_results.json,charts/*.png}`
  on disk.
- **Who said what, and who didn't**: the Analytics tab. See next section.

## Analytics: who said what

The Analytics tab (`GET /api/surveys/{id}/analytics`) is the single place
to see the whole panel's actual weight-elicitation responses side by side,
and to see honestly which configured agents *didn't* produce a response
and why, rather than only being able to check one agent's Trace at a
time, or inferring non-response from an agent's absence in the results
table.

It shows three things, computed purely from what's on disk (never
fabricated for an agent that didn't produce a result):

1. **Panel participation**: a count of every configured agent by status:
   `contributed` (at least one accepted sample), `zero_accepted` (ran to
   completion but every sample was rejected by guardrails), `pending_manual`
   (a `provider: manual` agent still waiting for a pasted-back response),
   `skipped` (the orchestrator caught a provider/permission/agent-card
   error, most commonly a missing API key, before any sample could be
   attempted), or `not_run` (configured but the survey has never been run).
2. **Best/Worst pick frequency**: across every accepted sample, how many
   times each criterion was picked Best and how many times Worst: the
   fastest way to see which dimension the panel actually converged on
   before even looking at the solved posterior weights.
3. **Weight elicitation details: who said what**: one row per accepted
   sample (agent, role, model, RAG on/off, Best, Worst, reasoning), and a
   second table for every non-contributing agent with its status and the
   specific reason (e.g. "every one of 15 attempts was rejected by
   guardrails" vs. "no result.json was ever written, missing API key").

See `web/backend/analytics.py` (`compute_analytics`) for the exact
classification logic and `tests/test_web_analytics.py` for the cases it's
tested against.

## Remote-LLM mode

Run this app on your own machine while the LLM calls run on a separate
Ollama host (e.g. the veritas server, over Tailscale), so LLM compute load
stays off your machine and iteration stays fast locally.

**CLI:**

```bash
export OLLAMA_BASE_URL=http://100.77.119.21:11434   # the server's Tailscale IP
PYTHONPATH=src python -m agentic_survey.cli run surveys/bsi-hawc-bwm
```

Everything else (the Bayesian solve, guardrails, storage) runs locally
regardless of where `OLLAMA_BASE_URL` points; only the `ollama`-provider
HTTP calls leave the machine. See `.env.example`.

**Web UI:** use the **Settings** page rather than an environment variable.
It's a runtime setting, not just a documented env var: switching it takes
effect on the very next survey run, no backend restart required. Pick a
preset (Local / Veritas server (Tailscale)) or enter a custom URL, click
"Test connection" to confirm the host is reachable and see which models it
has pulled, then Save. The choice persists across backend restarts
(`web/backend/data/llm_settings.json`, gitignored, machine-specific: not
something to commit or share). See `GET/PUT /api/settings/llm` and
`GET /api/settings/llm/test` if driving this from a script instead of the
UI.

Why this needed a settings page instead of just an env var: the CLI is a
fresh process every run, so it re-reads `OLLAMA_BASE_URL` every time. The
web backend is a long-lived process: without `routers/settings.py` and
`providers.reset_provider()`, whatever `OLLAMA_BASE_URL` was set to at
backend startup would be stuck for the process's whole life. See
`docs/development/changelog.md`'s 2026-08-02 "LLM-endpoint settings" entry.

## The Agent Card

project-cogtwins (VERITAS's precursor project) documents wanting exactly
this kind of portable agent spec in its URD (Amendment v2.0, S19, "Agent
Identity & Policy Enforcement") but never built one: its agents are
Python objects assembled from a hardcoded registry plus two Postgres
tables, not a file anyone can pick up and replicate. This is that file.

```json
{
  "schema_version": "1.0",
  "agent_id": "bim-coordinator-rag-ollama",
  "role": "BIM Coordinator",
  "role_description": "...",
  "instrument": "bwm",
  "system_prompt_template": "config/prompts/expert_panel_system.txt",
  "tools": [],
  "model": {"provider": "ollama", "name": "qwen2.5:14b", "temperature": 0.7, "seed": 42, ...},
  "rag": {"enabled": true, "corpus_path": "surveys/.../rag_corpora/bim-coordinator", ...},
  "sampling": {"repeats": 5, "max_retries_on_malformed": 2, ...},
  "permissions": {"data_scopes": ["surveys/.../rag_corpora/bim-coordinator/**"], "allowed_providers": ["ollama"]},
  "guardrails": {"schema_validation": true, "denylist_patterns": ["ignore (all|any|the) previous instructions", ...]},
  "did": {"method": "did:key", "id": "did:key:z6Mk...", "deterministic": true, "seed_derivation": "sha256('<seed>:bim-coordinator-rag-ollama')"},
  "environment": {"runtime": "sage", "runtime_version": "0.1.0", "python_version": "3.11.15", ...}
}
```

The identity mechanism (`did_key.py`) is a direct port of project-cogtwins's
own `veritas/svc-query/identity.py` pattern: deterministic Ed25519 keypair
via `sha256(seed:agent_id)`, encoded as a W3C `did:key`, with
Ed25519Signature2020-style Verifiable Credential issuance/verification
available (`AgentIdentity.issue_credential` / `verify_credential`) for
signing a specific agent response if a survey needs that level of
attributability. The one difference from cogtwins: the seed *derivation*
is documented inside the card itself (`did.seed_derivation`), so replaying
an agent only requires the card plus the shared seed value, not an
out-of-band process for finding out how the DID was made.

Security note, carried over unchanged from cogtwins: a deterministic DID is
a reproducibility property, not a security one. Anyone who learns the seed
can reconstruct the private key. Use `deterministic_did=False` in
`agent_card.new_card()` for any agent whose identity must resist
impersonation by someone who has seen its card.

## Manual paste-in agents

For a model with no API (Gemini/GPT web chat), set `model.provider:
"manual"` and `model.name` to whatever you'd call it in the report (e.g.
`"gemini-2.5-pro"`). First run:

```bash
PYTHONPATH=src python -m agentic_survey.cli run surveys/bsi-hawc-bwm
```

prints "Waiting on manually-pasted responses" and writes each pending
sample's exact prompt to
`surveys/<id>/agents/<agent-id>/manual_input/prompt_NN.md`. Paste that
into the model's chat UI, paste the reply into the matching
`response_NN.txt` in the same folder, and re-run: already-answered
samples are never re-asked, and nothing is skipped or invented if you stop
partway through.

## Why this exists, and what it fixed

`bsi-survey-app`'s Bayesian BWM solver was checked line-by-line against the
original author's (Majid Mohammadi) reference JAGS model before this app
adopted it as its solver. The classical BWM linear program and consistency-
index table were exactly correct. The Bayesian hierarchical model's
structure was also correct, but its concentration hyperprior was
`Gamma(1, 0.01)` (mean 100) where the reference model uses a diffuse,
near scale-free `Gamma(0.01, 0.01)` (mean ~1). The former biases posteriors
toward artificially narrow credible intervals, i.e. towards looking more
confident about expert agreement than the data supports, which defeats the
entire point of using a Bayesian method over the classical point-estimate
one. This is fixed at the source in `src/agentic_survey/solvers/bwm_bayesian.py`.

Every bug found since (timeout tuning, per-agent failure isolation, the
manual provider's sample-index tracking, the negative-error-bar chart
crash) is logged with its root cause in `docs/development/diagnostics.md`;
check there before re-diagnosing something that already has a documented
cause.

## Adding an agent

Copy an existing card under `surveys/<survey-id>/agents/`, change
`agent_id`, `role`, `role_description`, `model.provider`/`model.name`, and
`rag.enabled`/`permissions.data_scopes`. Regenerate its `did` block with
`agent_card.new_card(...)` (don't hand-edit the DID fields) or simply
delete them and let the orchestrator recompute on next load. Nothing else
needs to change; the orchestrator discovers every `*.json` file in that
directory.

## Adding a provider

Implement `agentic_survey.providers.base.LLMProvider` (one `complete()`
method) and register it in `agentic_survey/providers/__init__.py`.

## Adding an instrument

Implement `agentic_survey.instruments.base.Instrument` (`build_messages` +
`parse`) and register it in `agentic_survey/orchestrator.py`'s `INSTRUMENTS`
dict. The agent, provider, guardrail, and storage layers do not change.

## Status / what's deferred

This is a working core plus a web UI MVP, not the full long-term spec.
Deferred to follow-up work: a resolvable `did:web` variant (current DIDs
are `did:key`, self-certifying but not resolvable via HTTP), a full
Cedar/OPA-style policy evaluator for `permissions` (currently a direct
glob/allowlist check, not a general policy engine), an AHP instrument,
richer inter-sample agreement metrics for the guardrail's
agreement-threshold gate, drawio-based architecture diagrams in the
generated report, structural (not text-pattern) PDF/DOCX parsing, and
UI polish (dark-themed chart rendering, agent-selection for partial
survey runs, an "add agent from template" flow).

## Documentation

- `docs/development/changelog.md` for what changed and when.
- `docs/development/diagnostics.md` for bugs found, root cause, and fix.
- `.claude/rules/project-details.md` for this project's relationship to
  VERITAS-AIDB, BSI/TrustRoute, and project-cogtwins, plus the roadmap.
- `.claude/rules/documentation-maintenance.md` for the rule (binding on any
  AI agent working in this repo) that this README and `changelog.md` must
  be updated in the same change as any code change they describe.

### Keeping this README and the changelog current

This README (setup, repository structure, main-files tables, how-it-works
pipeline) and `docs/development/changelog.md` describe the repo as it
actually is right now. Whenever a change adds, removes, renames, or
meaningfully alters a file, endpoint, or workflow described here, update
the relevant section of this README in the same change, and add a dated
entry to `changelog.md` (with a `diagnostics.md` entry too, if the change
was a bug fix). See `.claude/rules/documentation-maintenance.md`.

## Related

- `docs/research/Work-in-progress/potential-papers/00-bsi/` (project-veritas)
  for the BSI paper and its HAWC-BWM methodology section.
- `docs/research/Work-in-progress/potential-papers/00-bsi/survey-app/` for
  the original `bsi-survey-app` this project generalises from.
- `~/ProgramFiles/project-cogtwins`, `veritas/svc-query/identity.py`, for
  the did:key + Verifiable Credential pattern this project's identity
  layer is ported from.
