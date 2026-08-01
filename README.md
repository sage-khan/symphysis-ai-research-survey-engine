# agentic-survey-tool

Config-driven agent panels for expert-elicitation surveys. Built as the
general-purpose successor to VERITAS's `bsi-survey-app`, starting from the
BSI paper's HAWC-BWM (Human-AI Weighted Consensus Best-Worst Method) use
case, but designed so a survey can plug in a different instrument (AHP,
etc.) without touching the agent, provider, or storage layers.

## What it does

1. **Spawns configured agents.** Every agent is a role (e.g. "BIM
   Coordinator"), a model + hyperparameters, an optional RAG corpus, and a
   sampling policy, all defined in a YAML config file. No prompt, model
   name, temperature, or seed is hardcoded in Python.
2. **Runs an instrument against each agent.** The instrument owns the prompt
   construction and response schema; agents don't know or care which
   instrument they're completing. `bwm` (Best-Worst Method) is implemented;
   the interface (`src/agentic_survey/instruments/base.py`) is designed for
   AHP and others to be added the same way.
3. **Applies guardrails.** Every response is schema-validated and
   rejected/re-sampled on malformed output; every agent is sampled multiple
   times (never a single completion treated as ground truth); every raw
   model completion (not just the parsed answer) is logged for audit.
4. **Solves and combines.** The classical BWM linear program (Rezaei, 2015)
   and the Bayesian hierarchical BWM (Mohammadi and Rezaei, 2020) are ported
   from `bsi-survey-app`, verified against the original author's reference
   JAGS implementation (github.com/Majeed7/BayesianBWM), and one real bug
   fixed in the process (see below). A parallel human-panel posterior can be
   combined with the agent-panel posterior via a draw-wise linear pool
   across a full alpha sensitivity sweep (HAWC-BWM).
5. **Persists everything per survey, per agent.** See "Project layout" below.
6. **Reports.** Markdown report plus matplotlib charts (posterior weights
   with credible intervals, HAWC-BWM sensitivity sweep).

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

# Local model, no API key needed:
ollama pull llama3.1:8b

export ANTHROPIC_API_KEY=...   # only needed for agents configured with provider: anthropic
export OPENAI_API_KEY=...      # only needed for agents configured with provider: openai
export OPENROUTER_API_KEY=...  # only needed for agents configured with provider: openrouter

PYTHONPATH=src python -m agentic_survey.cli run surveys/bsi-hawc-bwm
```

Or dockerized:

```bash
docker compose up --build
```

Output lands in `surveys/bsi-hawc-bwm/report/report.md` and `.../charts/`.

## Project layout

```
config/
  prompts/                       # shared system-prompt templates (referenced by agent configs)
surveys/<survey-id>/
  survey.yaml                    # instrument, dimensions, HAWC-BWM weighting/sweep config
  agents/<agent-id>.yaml         # one config per agent: role, model, RAG, sampling
  rag_corpora/<role>/            # disclosed, held-out RAG corpus per role (see SOURCES.md inside)
  human_responses/               # per-expert JSON export (e.g. from LimeSurvey), for HAWC-BWM combination
  agents/<agent-id>/             # written at runtime:
    config.yaml                  #   copy of the config actually used
    did.json                     #   this agent's did:veritas:agent:<uuid>
    conversation.jsonl           #   every raw completion + rejection, one line each
    thoughts.md                  #   human-readable reasoning trace
    samples/sample_NN.{json,md}  #   each accepted, schema-valid response
    result.json                 #   this agent's accepted payloads + guardrail summary
  report/
    report.md
    combined_results.json
    charts/*.png
```

## Adding an agent

Copy an existing YAML under `surveys/<survey-id>/agents/`, change `id`,
`role`, `role_description`, `model.provider`/`model.name`, and `rag.enabled`.
Nothing else needs to change; the orchestrator discovers every `*.yaml` file
in that directory.

## Adding a provider

Implement `agentic_survey.providers.base.LLMProvider` (one `complete()`
method) and register it in `agentic_survey/providers/__init__.py`.

## Adding an instrument

Implement `agentic_survey.instruments.base.Instrument` (`build_messages` +
`parse`) and register it in `agentic_survey/orchestrator.py`'s `INSTRUMENTS`
dict. The agent, provider, guardrail, and storage layers do not change.

## Status / what's deferred

This is a first working core, not the full long-term spec. Deferred to
follow-up work: a resolvable W3C DID/VC scheme (current DIDs are stable
identifiers, not resolvable documents), an AHP instrument, richer
inter-sample agreement metrics for the guardrail's agreement-threshold
gate, and drawio-based architecture diagrams in the generated report.

## Related

- `docs/research/Work-in-progress/potential-papers/00-bsi/` (project-veritas)
  for the BSI paper and its HAWC-BWM methodology section.
- `docs/research/Work-in-progress/potential-papers/00-bsi/survey-app/` for
  the original `bsi-survey-app` this project generalises from.
