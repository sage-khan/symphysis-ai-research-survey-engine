# Survey rules: TrustRouter SLM Panel Run 1 -- Level L3e (Economic Value sub-parts)

This survey is **one of 7 sibling surveys** that together make up the
TrustRouter SLM Panel Run 1 (2026-09-01, model: qwen3:14b). The full
TrustRouter Best-Worst-Method elicitation has 7 comparison levels (L1, L2,
L3a-L3e); each level is run here as its **own independent, single-comparison-set
survey** rather than bundling all 7 into one completion.

**Why split this way (do not "helpfully" answer other levels):** local
models in the 7B-32B range reliably fail when asked to answer all 7 BWM
levels (up to 24 criteria) in a single completion -- missing criteria,
self-rating convention errors ("Best vs Best" rated 9 instead of 1), and
truncation. See this repo's docs/development/diagnostics.md for the full,
documented history of that failure mode. Splitting into one call per level
(this survey) reuses the already-proven-reliable single-level `bwm`
instrument shape instead.

**This survey's own level: L3e -- Economic Value sub-parts.**
The three sub-parts that decompose Economic Value (E) from L1: current marketplace demand, tokenisation/liquidity ease, and projected future demand.

Comparison set for this survey:
- **E_market** (Current marketplace demand): Existing buyers right now.
- **E_liquidity** (Tokenisation ease): How easy is tradeable tokenisation?
- **E_demand** (Future demand): Regulated / AI / digital-twin growth.

## Grounding rules (apply to every level, copied from the parent hierarchy survey)

1. Ground every comparison in what each criterion specifically means for a
   construction-project record considered for blockchain storage. See this
   survey's shared knowledge repository (`knowledge_repo/`) for the real
   survey instrument's canonical glossary, the concept-paper primer, and the
   research hypothesis this elicitation exists to test -- these are the
   ground truth for terminology, not a paraphrase.
2. TrustRouter's composite combines its top-level factors multiplicatively
   (`TrustRouter = DVS x F x (1 + E) x A`), not as a weighted sum -- see the
   concept-paper primer before answering L1 specifically.
3. Do not treat any one criterion as self-evidently more important than the
   others by default. Surface genuine professional judgement, not an
   assumed "obviously correct" ranking.
4. Answer as the professional you are configured to be would, on the merits
   of these criteria as construction-project data-trust factors.
5. Ground your Best/Worst choice and ratings in any reference material you
   were given (shared knowledge repository, your role's RAG corpus), citing
   it by its exact tag. If you were not given material for a specific
   point, reason from your own domain expertise and say so plainly.
6. Cite only real, verifiable, reputable sources (peer-reviewed papers,
   labelled preprints, standards documents, academic/institutional
   technical reports). Never cite or imply reliance on a blog, forum, or
   marketing page.
7. The Best-to-Others and Others-to-Worst ratings are RATIOS, not
   importance scores: Best compared to itself is always exactly 1 (one time
   as important as itself), never 9; the same applies to Worst compared to
   itself.
