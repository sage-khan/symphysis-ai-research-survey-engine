# Research notes: security and related-work context

Short notes linking Symphysis's design to external literature surfaced during a VERITAS-AIDB
literature-review pass (30 August 2026). Not a systematic review; each item below is flagged
because it maps to a specific, named mechanism in this codebase. Cite as `<title>, <author> et
al., <year>` with the arXiv ID; do not cite by any catalogue row number (see the shared
`project-veritas` house citation rule, applied here too since this repo is part of the same
project family).

## Security: permission enforcement can be attacked at the instruction layer, not just the data layer

`permissions.py` enforces (not merely documents) an Agent Card's `data_scopes` and
`allowed_providers` before any file is read or provider is called, and `guardrails.py` runs a
denylist regex scan against prompt-injection markers in every response. Both are the class of
defense examined in *When Context Gets Root: Privilege Escalation in LLM Harnesses*, He et al.,
2026, arXiv:2608.27299. That paper's core finding is that both the model-side instruction-
hierarchy defense (trusting system/user instructions over tool-level content) and a common
harness-side defense, an automatic permission reviewer that infers intent from tool output, can
both be defeated by the same attack: untrusted tool-level content (a document in a RAG corpus,
a web search result) engineered to be read by the harness as a legitimate instruction rather
than data.

Relevance to this codebase: every Symphysis agent that has `rag.enabled` or `tools:
["web_search"]` ingests exactly this kind of untrusted tool-level content before its guardrail
and QA-precheck layers run. The paper's attack targets the permission-review step itself, which
is architecturally close to what `permissions.check_provider_allowed` / `check_data_scope` do
here. This does not mean the current implementation is vulnerable as described (the attack in
the paper targets harnesses that use an LLM-based permission reviewer to infer intent; this
codebase's `permissions.py` check is a deterministic scope-match, not an LLM inference step, so
the direct attack surface may not transfer), but it is a concrete, citable threat model worth
checking against before any future change makes permission decisions LLM-mediated rather than
deterministic.

## Design vocabulary: distinguishing error, hallucination, and deception in agent output

`qa_checks.py`'s "Deterministic genuineness checks" (a QA-precheck restatement checked against
ground truth, and a `sources_used` claim checked against what was actually available in the
prompt, flagging a fabricated citation) is exactly the kind of check that *Can AI Lie? The
Difference Between Error, Hallucination, and Deception*, Peretz, 2026 (Andy Agent Lab,
practitioner article, non-academic source, not independently peer-reviewed, cite only as
background reading, never as a scientific-paper citation) argues needs separating out: an agent
that is wrong is not the same
as an agent that fabricates a source it never had access to, which is not the same as an agent
that deliberately misrepresents its own state. Useful vocabulary for describing what the QA
precheck and fabricated-citation flag are actually distinguishing, in documentation or in a
future paper about this system's trust design; not a citable scientific source on its own.

## Related work: other systems using AI agents to stand in for parts of the research process

Two 2026 systems address an adjacent problem (using AI agents to accelerate or stand in for
parts of the scientific research process, rather than expert-elicitation surveys specifically)
and are worth knowing about as design precedent or comparison points if this project's own
design rationale is ever written up:

- *Accelerating Scientific Research with Gemini in the Real-World*, Schmidgall et al., 2026,
  arXiv:2608.26701 (the Co-Scientist extension paper): a Gemini-based multi-agent system for
  end-to-end scientific research (hypothesis generation through manuscript writing), validated
  across materials science, oncology, and metabolic-disorder research with execution-grounded,
  closed-loop lab integration. Different mechanism (autonomous hypothesis-to-experiment loop,
  not expert-panel emulation) but the same broader problem space: AI systems substituting for
  scarce human research capacity.
- *Build Your Personalized Research Group: A Multiagent Framework for Continual and Interactive
  Science Automation*, Li et al., 2025, arXiv:2510.15624 (introduces `freephdlabor`,
  open-source at github.com/ltjed/freephdlabor), which explicitly argues
  that prior AI-scientist systems fail on two points relevant here: rigid pipelines that cannot
  adapt mid-run, and context-window overload across a long-horizon research process. Symphysis
  sidesteps both by design (each agent is stateless per survey round, driven by a fixed
  instrument rather than an adaptive plan), which is itself worth stating explicitly as a design
  choice if this system's rationale is ever compared against that class of system.

## Security: propagation risk across a shared agent population

Every agent in a Symphysis survey can read the survey's shared knowledge repository (uploaded
once, available to every agent automatically), and every agent's behavior is driven by its own
plus a global rulefile. *Mind Viruses: Self-Propagating Ideas in Multi-Agent LLM Systems*,
Papadopoulos et al., 2026, arXiv:2608.10218 (Anthropic Fellows Program, EPFL, Anthropic), shows
that a goal or idea can propagate agent-to-agent through ordinary communication in exactly this
kind of shared-substrate multi-agent setup, and that idle or under-specified agents are more
susceptible while a short explicit warning in an agent's system prompt confers near-total
immunity. The paper's own authors name this class of risk as directly relevant to
"Symphysis-style multi-agent deployment." A cheap, concrete mitigation worth considering: adding
an explicit anti-propagation warning to `config/global_rulefile.md`, applied to every agent by
the same mechanism that already appends it to every system prompt.

## Design precedent: rubric-based judging with human calibration

*Training AI Scientists to Replicate Research*, Falck et al., 2026, arXiv:2608.13331 (Inherent
Laboratories), trains an agent to replicate figures from published papers, scored by an
auto-generated per-task rubric judge whose reward signal was validated against human expert
rankings before being trusted. That validate-against-humans-before-trusting discipline is the
same shape as this codebase's own reference-implementation verification of the Bayesian
hierarchical BWM solver (verified against Mohammadi and Rezaei's original JAGS implementation,
see `docs/development/diagnostics.md`). The paper's own explicit caution, that a rubric judge
validated on one task distribution should not be assumed valid on a distribution it was never
checked against, is a directly applicable caution for any future change to Symphysis's own
instrument-scoring logic: a new instrument or a materially different survey domain should not
inherit an existing rubric/QA-precheck's validation without rechecking it.

See `docs/research/Work-in-progress/potential-papers/` in the `project-veritas` repo for the
full literature catalogue these were drawn from (`LITERATURE_REVIEW_CATALOG_2.csv` rows
S3066, S3068, S3071; `LITERATURE_REVIEW_CATALOG.csv` rows S2791, S2823;
`Non-academic-literature-catalog.csv` row S1004).
