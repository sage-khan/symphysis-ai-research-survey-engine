# Survey rules: TrustRouter Agentic Full Panel -- Level L3d (Attack Resistance sub-parts)

This survey is **one of 7 sibling surveys** that together make up the TrustRouter Agentic
Full Panel run (model: llama3.1:8b, runtime_backend: openmanus). Each level runs as its own
independent, single-comparison-set survey, answered via the OpenManus-backed "bwm_two_stage"
flow (two plain, non-tool-calling completions per agent: best/worst, then dynamically-built
pairwise ratings) rather than a single tool call.

**This survey's own level: L3d -- Attack Resistance sub-parts.**
The three sub-parts that decompose Attack Resistance (A) from L1.

Comparison set for this survey:
- **A_sybil** (Sybil resistance): Fake-identity attacks.
- **A_oracle** (Oracle resistance): Sensor and device tampering.
- **A_insider** (Insider resistance): Malicious legitimate access.

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
