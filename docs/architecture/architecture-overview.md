# Symphysis architecture diagrams

Three diagrams, each `.drawio` source next to its rendered `.png` export,
per this repo's diagram convention. Regenerate a PNG after editing a
`.drawio` file with:

```bash
drawio --export --format png --scale 1.5 --output <name>.png <name>.drawio
```

## current-system-architecture

The real pipeline as actually implemented today, laid out as seven
sequential stages: Preflight, Configuration, Grounding, Verification
before answering, Execution, Verification after answering, and Synthesis
and trust. This is what one `symphysis run` actually does, end to end:
the upfront provider-reachability check (before any agent is spawned),
then one agent's run through `orchestrator.run_survey`, including the QA
precheck, the four possible context sources (RAG, shared knowledge,
role packs, and web search, now backed by self-hosted SearXNG + Crawl4AI
rather than the earlier Tavily integration), guardrails, the sources-used
citation check, both BWM solvers, and the SHA-256 integrity manifest.
Read this diagram to understand what the system does today, not what it
is planned to do.

## agent-card-anatomy

A structural reference for the Agent Card: the one portable JSON file
that fully defines a spawnable agent (`agent_card.py`). Nine field
categories (Identity, Decentralized Identity, Model, Grounding, Sampling,
Permissions, Guardrails, Behavior, Environment), each listing its actual
fields. Given the same JSON and the shared DID seed, an identical agent
can be respawned anywhere without reading this app's source, which is the
design property this diagram documents.

## target-pipeline-vision

The layered research-workflow vision this project is working toward
(Researcher layer, Orchestration layer, AI panel layer, Collaboration
layer, Output and export layer), with every box color-coded by its real
implementation status: green border for implemented today, amber for
partially implemented, dashed red for planned future work. This diagram
is deliberately honest about the gap between the vision and the current
build; do not read a box's presence here as a claim that it exists yet.
The most significant planned gap is multi-agent debate: today's agents
answer independently in every case, and the Consensus and Confidence
boxes are produced by combining those independent answers statistically
(BWM posterior combination), not by agents negotiating disagreement with
each other.

## Source

The initial sketch for the target pipeline vision came from a plain-text
flowchart description of the intended researcher-facing workflow. These
three diagrams formalize that sketch, correct it against what the system
actually implements today (see `current-system-architecture` and
`agent-card-anatomy` for the ground truth), and extend it with the
verification and trust mechanisms (QA precheck, sources-used check,
integrity manifest) that were not part of the original sketch.
