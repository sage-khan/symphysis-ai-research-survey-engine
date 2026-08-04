---
trigger: always_on
---

# Symphysis (AI Research Survey Engine): Project Details

## Overview

**Symphysis** is a trust-first, local-first, secure AI survey-agent engine
for expert-elicitation research: it runs structured survey instruments
(Best-Worst Method, Analytic Hierarchy Process, and hierarchical
variants) against a panel of individually configured AI agents, alongside
or in place of a human panel. Every agent is fully defined by one portable
JSON file (an "Agent Card": `did:key` identity, model, hyperparameters,
RAG corpus, permissions, guardrails), spawned against a pluggable
instrument, and produces a full plain-text trace (every prompt sent,
every tool call made, every raw completion, every accepted and rejected
sample, and a human-readable filled-in survey) so nothing about how a
result was produced is opaque or locked into this app.

It exists for a specific research bottleneck: assembling a large enough,
sufficiently diverse *human* expert panel is often the actual constraint
on an expert-elicitation study, not the method. Symphysis lets an AI
panel stand in for, or alongside, a human panel without giving up
reproducibility or trustworthiness, which matters most exactly where
human-in-the-loop input is scarcest: niche technical specialties,
sensitive or proprietary corpora, and research budgets that cannot fund
a large expert panel. It is a standalone, general-purpose project: any
survey, any instrument, any mix of human and AI-agent respondents, not
scoped to one paper or one research programme.

Earlier session records and `docs/development/changelog.md` history
predate this repository's final name and refer to it as
`agentic-survey-tool` or `SAGE`; `symphysis` is now the only name used
anywhere in this codebase, including the internal Python package
(`src/symphysis/`) and PyPI distribution.

**Owner:** Muhammad Danyal (Sage) Khan (`dan@go.ugr.es`)
**Repository:** `github.com/sage-khan/symphysis-ai-research-survey-engine`
**Status:** Early, active development. Core (agents, providers, BWM/AHP/
hierarchical-BWM instruments, guardrails, solvers, reporting) is built and
tested; the web UI and multi-format survey parsing are being added.
Planned for open-source release (Apache 2.0) on its own terms.

Do not hardcode any specific survey's domain logic (dimension names, gate
conditions, weighting thresholds) into this app as defaults; that belongs
entirely to that survey's own `survey.yaml` and Agent Cards under
`surveys/`, precisely so this app stays usable for a differently-shaped
survey without any code change. `surveys/trustrouter-hawc-bwm/` is one
worked example (a real hierarchical Best-Worst Method elicitation), not a
built-in assumption.

## Architecture Summary

See the root `README.md` for the full picture; in short:

- **Agent Card** (`agent_card.py`): the portable JSON spec for one agent.
- **Providers** (`providers/`): Ollama, Anthropic, OpenAI, OpenRouter, and a
  `manual` provider for models with no API (paste-in web chat responses).
- **Instruments** (`instruments/`): own prompt construction and response
  schema; `bwm`, `ahp`, and `hierarchical_bwm` are implemented, others plug
  in the same way.
- **Guardrails** (`guardrails.py`, `permissions.py`): schema validation,
  denylist scanning, repeated sampling, enforced (not just documented)
  data-scope and provider allowlists.
- **Solvers** (`solvers/`): classical and Bayesian Best-Worst Method and
  Analytic Hierarchy Process, verified against the original authors'
  reference implementations.
- **Storage** (`storage.py`): the full per-agent trace (prompt, tool calls,
  raw completions, rejections, reasoning, a consolidated filled-survey
  document) plus the per-survey combined report, all plain Markdown/JSON.

## Roadmap (living, update as work lands)

- [x] Core: Agent Cards, providers, BWM/AHP/hierarchical-BWM instruments,
      guardrails, solvers, Docker deployment, live-tested across 6 Ollama
      model families plus Claude Opus/Sonnet/Haiku and manual Gemini/GPT.
- [x] Remote-LLM mode: point `OLLAMA_BASE_URL` at a remote Ollama host
      (e.g. over Tailscale) and run the rest of the pipeline locally.
- [x] Web UI MVP (FastAPI + React): survey upload/parsing (structured
      Markdown and LimeSurvey `.lss` well-supported, PDF/DOCX best-effort),
      agent configuration/creation/edit screens, run + results view with
      per-agent trace (filled survey, reasoning, prompt, conversation log),
      downloadable `.zip` output. Verified end to end in a real browser
      (Playwright).
- [x] Packaged and published to PyPI as `symphysis`, with a Typer CLI
      (`new`, `add-agent`, `run`, `report`, `fix-survey`).
- [x] Self-hosted web search (SearXNG + Crawl4AI), no external API key
      required.
- [ ] UI polish: dark-themed chart rendering, partial-roster survey runs
      (select which agents to include per click, not always "all"),
      structural PDF/DOCX parsing.
- [ ] `did:web` option alongside `did:key` for agents that need a
      resolvable identity document.

## Contact

Primary: Muhammad Danyal Khan, `dan@go.ugr.es`.

## Data Integrity: No Fabricated Results (mandatory, no exceptions)

Every sample this tool reports must be a real completion from the provider named
in its Agent Card, obtained by actually calling that provider, or the run must
fail/skip visibly (`error`, `pending_manual`, or a "skipped agents" notice), never
silently substituted with placeholder, templated, or hand-written text
presented as a model output. This applies with equal force to code written for
this repo and to any one-off script or manual step run against it: if a
provider is uncredentialed, unreachable, or too slow to finish in the time
available, the correct response is to report that plainly (which agents ran,
which were skipped and why, how many samples were accepted vs rejected by
guardrails), not to invent numbers so a run "looks complete."

The `trustrouter-hawc-bwm` example survey's `human_responses/experts.SYNTHETIC.json`
is intentionally named and commented as a placeholder for pipeline testing;
never let a report or paper draft describe HAWC-BWM combined weights computed
against it as real human data. Any survey whose results are destined for
publication must state plainly, in the run's own report and in whatever
document cites it, whether the human side is real survey-export data or
the synthetic placeholder, and whether every listed agent actually ran or
was skipped/pending.

**Why:** standing instruction from Dan: "You are NEVER allowed to fake
results and do half hearted implementation. Be truthful throughout the
process," given explicitly because agent-panel results from this tool can
feed real published research. **How to apply:** before reporting any
run's results to Dan or writing them into a paper, check the run's
report.md "Skipped agents" / "Waiting on manually-pasted responses"
sections and carry that caveat forward rather than quietly dropping it.
