# Survey rules: TrustRouter Claude CLI Panel -- Level L2 (Six trust dimensions inside DVS)

This survey is **one of 7 sibling surveys** that together make up the TrustRouter Claude CLI
Panel run (model: haiku, provider: claude_cli, runtime_backend: direct_completion). Each
level runs as its own independent, single-comparison-set survey, answered via a single
structured-JSON completion (the flat "bwm" instrument), not the two-turn agentic flow used for
the local SLM phases.

**This survey's own level: L2 -- Six trust dimensions inside DVS.**
The six trust dimensions that make up the Data Value Score (DVS) factor from L1.

Comparison set for this survey:
- **Q** (Quality): Is the data technically clean?
- **PT** (Provenance Trust): Can we trust who produced it?
- **V** (Verification Strength): Cryptographic or audit-trail evidence?
- **IC** (Independent Confirmation): Do multiple independent parties agree?
- **L** (Legal Compliance): Is this data required or regulated?
- **C** (Criticality): How big is the impact if it is wrong?

## Grounding rules (apply to every level, copied from the parent hierarchy survey)

1. Ground every comparison in what each criterion specifically means for a
   construction-project record considered for blockchain storage. See this
   survey's shared knowledge repository (`knowledge_repo/`) for the real
   survey instrument's canonical glossary, the concept-paper primer, and the
   research hypothesis this elicitation exists to test.
2. TrustRouter's composite combines its top-level factors multiplicatively
   (`TrustRouter = DVS x F x (1 + E) x A`), not as a weighted sum -- see the
   concept-paper primer before answering L1 specifically.
3. Do not treat any one criterion as self-evidently more important than the
   others by default.
4. Answer as the professional you are configured to be would, on the merits
   of these criteria as construction-project data-trust factors.
5. Ground your Best/Worst choice and ratings in any reference material you
   were given, citing it by its exact tag where possible.
6. Cite only real, verifiable, reputable sources. Never cite or imply
   reliance on a blog, forum, or marketing page.
