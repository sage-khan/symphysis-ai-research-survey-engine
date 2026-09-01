# Survey rules: TrustRouter Agentic Two-Stage Pilot (2026-09-01)

This is a **pilot run** proving the OpenManus-backed "bwm_two_stage" runtime flow end-to-end
through the real Symphysis engine (`symphysis run`), not an isolated test script. One agent,
one level (L1, the four top-level TrustRouter factors), `runtime_backend: openmanus`.

**Why this flow exists (do not "helpfully" answer differently):** asking mistral:7b to combine
free-text reasoning and a structured tool-call submission in one turn proved fragile (see this
repo's docs/development/diagnostics.md and project-veritas's
agentic-experiment-design-decisions.md, 2026-09-01 entries). This survey's agent instead
answers via two plain completions driven by the runtime itself (best/worst, then dynamically
built pairwise ratings) -- no tool call is issued for this instrument.

**This survey's level: L1 -- Top-level TrustRouter factors.**
The four top-level TrustRouter factors (DVS, F, E, A), combined multiplicatively as
TrustRouter = DVS x F x (1+E) x A. This comparison expresses relative importance among
multiplicatively-combined factors, not a share of one linear total.

Comparison set for this survey:
- **DVS** (Data Value Score): Composite trustworthiness of the data.
- **F** (Technical Feasibility Fit): How well the artefact fits ledger constraints (size,
  update rate, latency). F = 1 - P.
- **E** (Economic Value): Financial or asset value at stake if the data is corrupted or lost.
- **A** (Attack Resistance): Difficulty of undetected manipulation.

## Grounding rules

1. Ground every comparison in what each criterion specifically means for a construction-project
   record considered for blockchain storage. See this survey's shared knowledge repository
   (`knowledge_repo/`) for the real survey instrument's canonical glossary, the concept-paper
   primer, and the research hypothesis this elicitation exists to test.
2. TrustRouter's composite combines its top-level factors multiplicatively
   (`TrustRouter = DVS x F x (1 + E) x A`), not as a weighted sum.
3. Do not treat any one criterion as self-evidently more important than the others by default.
4. Answer as the professional you are configured to be would, on the merits of these criteria
   as construction-project data-trust factors.
5. Cite only real, verifiable, reputable sources. Never cite or imply reliance on a blog,
   forum, or marketing page.
