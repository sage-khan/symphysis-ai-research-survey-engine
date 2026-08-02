---
trigger: always_on
---

# agentic-survey-tool: Project Details

## Overview

**agentic-survey-tool** is a config-driven, replicable agent-panel platform
for expert-elicitation surveys. Every agent is fully defined by one portable
JSON file (an "Agent Card": identity, model, hyperparameters, RAG corpus,
permissions, guardrails), spawned against a pluggable instrument (Best-Worst
Method first, others to follow), and produces a full plain-text trace (every
prompt sent, every tool call made, every raw completion, every accepted and
rejected sample, and a human-readable filled-in survey) so nothing about how
a result was produced is opaque or locked into this app.

**Owner:** Muhammad Danyal (Sage) Khan (`dan@go.ugr.es`)
**Repository:** `github.com/sage-khan/agentic-survey-tool` (private)
**Status:** Early, active development. Core (agents, providers, BWM
instrument, guardrails, solvers, reporting) is built and tested; the web UI
and multi-format survey parsing are being added.

## Relationship to VERITAS-AIDB

This tool is the general-purpose successor to VERITAS's `bsi-survey-app`
(`project-veritas/docs/research/Work-in-progress/potential-papers/00-bsi/survey-app/`),
which implemented the Bayesian Best-Worst Method pipeline for exactly one
survey (the Blockchain Suitability Index dimension-weight elicitation) with
no agent-spawning capability. agentic-survey-tool generalises that pipeline
(the classical and Bayesian BWM solvers are ported from it, verified against
the original author's reference implementation, with one real bug fixed in
the process) into a reusable platform: any survey, any instrument, any mix
of human and AI-agent respondents.

Its first and driving use case is **HAWC-BWM** (Human-AI Weighted Consensus
Best-Worst Method): the methodology section of VERITAS's **TrustRoute**
paper (`docs/research/Work-in-progress/potential-papers/00-bsi/`, formerly
titled "Blockchain Suitability Index") describes running a parallel,
disclosed synthetic expert panel alongside the human Bayesian BWM expert
elicitation, combined at a headline 60:40 human-to-agent ratio across a full
sensitivity sweep, as a triangulation and robustness check on the human
panel, never a replacement for it. This tool is the implementation of that
synthetic panel: it spawns the agent side of HAWC-BWM, while the human side
continues to run through the existing LimeSurvey instrument.

Do not fork, vendor, or duplicate BSI/TrustRoute-specific logic (the six
trust dimensions, the gate conditions, the storage-routing thresholds) into
this repo as hardcoded defaults; those belong to the `bsi-hawc-bwm` example
survey under `surveys/`, expressed entirely through Agent Cards and
`survey.yaml`, precisely so this app stays usable for a differently-shaped
survey without any code change.

Its identity layer (`did_key.py`: deterministic Ed25519 keypairs encoded as
W3C `did:key`, with Ed25519Signature2020-style Verifiable Credential
issuance) is ported from project-cogtwins's `veritas/svc-query/identity.py`,
the one piece of that project's agent-identity design that was actually
built and verified working, as opposed to the capability-scoped "Agent
Passport" layer that project's own URD documents wanting but never
implemented. The portable, single-file Agent Card this repo builds on top of
that identity layer is, correspondingly, the piece CogTwins itself does not
have.

## Architecture Summary

See the root `README.md` for the full picture; in short:

- **Agent Card** (`agent_card.py`): the portable JSON spec for one agent.
- **Providers** (`providers/`): Ollama, Anthropic, OpenAI, OpenRouter, and a
  `manual` provider for models with no API (paste-in web chat responses).
- **Instruments** (`instruments/`): own prompt construction and response
  schema; `bwm` is implemented, others plug in the same way.
- **Guardrails** (`guardrails.py`, `permissions.py`): schema validation,
  denylist scanning, repeated sampling, enforced (not just documented)
  data-scope and provider allowlists.
- **Solvers** (`solvers/`): classical and Bayesian Best-Worst Method,
  verified against the original authors' reference implementations.
- **Storage** (`storage.py`): the full per-agent trace (prompt, tool calls,
  raw completions, rejections, reasoning, a consolidated filled-survey
  document) plus the per-survey combined report, all plain Markdown/JSON.

## Roadmap (living, update as work lands)

- [x] Core: Agent Cards, providers, BWM instrument, guardrails, solvers,
      Docker deployment, live-tested on the veritas server (6 Ollama model
      families + Claude Opus/Sonnet/Haiku + manual Gemini/GPT).
- [x] Remote-LLM mode: point `OLLAMA_BASE_URL` at the veritas server over
      Tailscale and run the rest of the pipeline locally.
- [x] Web UI MVP (FastAPI + React): survey upload/parsing (structured
      Markdown and LimeSurvey `.lss` well-supported, PDF/DOCX best-effort),
      agent configuration/creation/edit screens, run + results view with
      per-agent trace (filled survey, reasoning, prompt, conversation log),
      downloadable `.zip` output. Verified end to end in a real browser
      (Playwright), including the exact "re-run after pasting a manual
      response, same server process" scenario that surfaced the
      sample-index bug fixed in diagnostics.md.
- [ ] UI polish: dark-themed chart rendering, partial-roster survey runs
      (select which agents to include per click, not always "all"),
      structural PDF/DOCX parsing.
- [ ] AHP instrument (BWM was first by necessity, not by design; the
      instrument interface was built to make this a config addition, not a
      rewrite).
- [ ] `did:web` option alongside `did:key` for agents that need a
      resolvable identity document.

## Contact

Primary: Muhammad Danyal Khan, `dan@go.ugr.es`.

## Data Integrity: No Fabricated Results (mandatory, no exceptions)

Every sample this tool reports must be a real completion from the provider named
in its Agent Card, obtained by actually calling that provider, or the run must
fail/skip visibly (`error`, `pending_manual`, or a "skipped agents" notice) --
never silently substituted with placeholder, templated, or hand-written text
presented as a model output. This applies with equal force to code written for
this repo and to any one-off script or manual step run against it: if a
provider is uncredentialed, unreachable, or too slow to finish in the time
available, the correct response is to report that plainly (which agents ran,
which were skipped and why, how many samples were accepted vs rejected by
guardrails), not to invent numbers so a run "looks complete."

The `bsi-hawc-bwm` example surveys

## Data Integrity: No Fabricated Results (mandatory, no exceptions)

Every sample this tool reports must be a real completion from the provider named
in its Agent Card, obtained by actually calling that provider, or the run must
fail/skip visibly (`error`, `pending_manual`, or a "skipped agents" notice) --
never silently substituted with placeholder, templated, or hand-written text
presented as a model output. This applies with equal force to code written for
this repo and to any one-off script or manual step run against it: if a
provider is uncredentialed, unreachable, or too slow to finish in the time
available, the correct response is to report that plainly (which agents ran,
which were skipped and why, how many samples were accepted vs rejected by
guardrails), not to invent numbers so a run "looks complete."

The `bsi-hawc-bwm` example survey's `human_responses/experts.SYNTHETIC.json`
is intentionally named and commented as a placeholder for pipeline testing;
never let a report or paper draft describe HAWC-BWM combined weights computed
against it as real human data. Any survey whose results are destined for a
paper (TrustRoute or otherwise) must state plainly, in the run's own report
and in whatever document cites it, whether the human side is real LimeSurvey
export data or the synthetic placeholder, and whether every listed agent
actually ran or was skipped/pending.

**Why:** standing instruction from Dan (2026-08-03): "You are NEVER allowed
to fake results and do half hearted implementation. Be truthful throughout
the process," given explicitly because these agent-panel results feed the
TrustRoute paper. **How to apply:** before reporting any run's results to
Dan or writing them into a paper, check the run's report.md "Skipped
agents" / "Waiting on manually-pasted responses" sections and carry that
caveat forward rather than quietly dropping it.
