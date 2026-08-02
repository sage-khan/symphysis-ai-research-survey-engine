# agentic-survey-tool

Config-driven, replicable agent panels for expert-elicitation surveys.
Built as the general-purpose successor to VERITAS's `bsi-survey-app`,
starting from the BSI paper's HAWC-BWM (Human-AI Weighted Consensus
Best-Worst Method) use case, but designed so a survey can plug in a
different instrument (AHP, etc.) without touching the agent, provider, or
storage layers.

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
   fixed in the process (see below). A parallel human-panel posterior can be
   combined with the agent-panel posterior via a draw-wise linear pool
   across a full alpha sensitivity sweep (HAWC-BWM).
7. **Persists everything per survey, per agent.** See "Project layout" below.
8. **Reports.** Markdown report plus matplotlib charts (posterior weights
   with credible intervals, HAWC-BWM sensitivity sweep).

## The Agent Card

project-cogtwins (VERITAS's precursor project) documents wanting exactly
this kind of portable agent spec in its URD (Amendment v2.0, S19, "Agent
Identity & Policy Enforcement") but never built one -- its agents are
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
  "environment": {"runtime": "agentic-survey-tool", "runtime_version": "0.1.0", "python_version": "3.11.15", ...}
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
`response_NN.txt` in the same folder, and re-run -- already-answered
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

## Quick start

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
(Qwen, Gemma, Llama, Mistral, DeepSeek, Phi -- one per domain-persona role,
so base-vs-RAG comparisons hold the model constant within a role) plus a
5-agent "independent reviewer" cross-check tier (Claude Opus/Sonnet/Haiku
via the Anthropic API, and manually-pasted Gemini/GPT).

## Project layout

```
config/
  prompts/                       # shared system-prompt templates (referenced by agent cards)
surveys/<survey-id>/
  survey.yaml                    # instrument, dimensions, HAWC-BWM weighting/sweep config
  agents/<agent-id>.json         # the portable Agent Card (source config, see above)
  rag_corpora/<role>/            # disclosed, held-out RAG corpus per role (see SOURCES.md inside)
  human_responses/               # per-expert JSON export (e.g. from LimeSurvey), for HAWC-BWM combination
  agents/<agent-id>/             # written at runtime:
    card.json                    #   copy of the card actually used for this run
    did.json                     #   this agent's did:key + public key (from the card)
    manual_input/                #   provider: manual agents only -- prompt_NN.md / response_NN.txt
    conversation.jsonl           #   every raw completion + rejection, one line each
    thoughts.md                  #   human-readable reasoning trace
    samples/sample_NN.{json,md}  #   each accepted, schema-valid response
    result.json                  #   this agent's accepted payloads + guardrail summary
  report/
    report.md
    combined_results.json
    charts/*.png
```

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

This is a first working core, not the full long-term spec. Deferred to
follow-up work: a resolvable `did:web` variant (current DIDs are `did:key`,
self-certifying but not resolvable via HTTP), a full Cedar/OPA-style policy
evaluator for `permissions` (currently a direct glob/allowlist check, not a
general policy engine), an AHP instrument, richer inter-sample agreement
metrics for the guardrail's agreement-threshold gate, and drawio-based
architecture diagrams in the generated report.

## Related

- `docs/research/Work-in-progress/potential-papers/00-bsi/` (project-veritas)
  for the BSI paper and its HAWC-BWM methodology section.
- `docs/research/Work-in-progress/potential-papers/00-bsi/survey-app/` for
  the original `bsi-survey-app` this project generalises from.
- `~/ProgramFiles/project-cogtwins`, `veritas/svc-query/identity.py`, for
  the did:key + Verifiable Credential pattern this project's identity
  layer is ported from.
