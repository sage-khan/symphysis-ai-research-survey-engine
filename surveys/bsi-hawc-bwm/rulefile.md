# Survey rules: TrustRouter/BSI Full Hierarchy Weight Elicitation

This survey elicits Best-Worst Method weights across the complete real
TrustRouter/Blockchain Suitability Index (BSI) framework, not a subset of
it: seven separate comparison levels covering the top-level composite
(DVS, F, E, A), the six trust dimensions inside DVS (Q, PT, V, IC, L, C),
and the further breakdowns of Q, PT, V, A, and E into their own
sub-criteria. See the composite formula and per-level structure in this
survey's own prompt; do not assume any one level (for example, the six
dimensions inside DVS) is "the whole calculation." These rules apply in
addition to the global rules; they exist to keep every agent's judgement
grounded in this specific framework, not a generic notion of "data trust."

## What you have been given as reference material

This survey's shared knowledge repository (available to every agent
regardless of your own dedicated RAG corpus setting) contains real
material, not a summary written to be convenient for this survey:

1. **A hypothesis document**
   (`trustrouter_research_hypothesis.md`): an extract, not a paraphrase,
   of the TrustRouter construction research paper's own stated research
   gap and contribution. This is the actual academic hypothesis your
   weight elicitation exists to test, not background color.
2. **The real survey file**
   (`bsi_expert_questionnaire_v5_real_survey_instrument.md`): the complete
   BSI Expert Questionnaire (v5, May 2026, Universidad de Granada /
   University of Ljubljana) as it was actually administered to the real
   15-expert human panel via LimeSurvey (survey 185662). Use its
   background section, canonical glossary, and Part 3 comparison framing
   as your primary reference for what each criterion means in this
   framework; it is the ground truth for terminology, not this rulefile's
   own paraphrase of it.
3. **A concept-paper primer**
   (`trustrouter_concept_paper_primer.md`): a plain-English walk-through of
   the full seven-level structure, the two-stage gate-then-score
   architecture, and why the top-level (L1) comparison is a different kind
   of "importance" than every other level.
4. Role-specific RAG corpora (per agent, if your card has RAG enabled):
   real, cited sources from the project's own literature catalogue,
   relevant to your specific role's slice of the hierarchy.

If further relevant domain material becomes available for a specific role
(construction standards, blockchain-trust literature, GDPR guidance) it
belongs in that role's own RAG corpus, cited by title/author/year, not
invented or summarized from memory.

## Grounding rules for every level

1. Ground every comparison in what each criterion specifically means for
   a construction-project record considered for blockchain storage, per
   the real survey instrument's canonical glossary, not a generic notion
   imported from another domain:
   - **Quality (Q)**: completeness, accuracy, and timeliness of the record
     itself; broken down further into Intrinsic, Contextual, and
     Representational quality (ISO 25012).
   - **Provenance Trust (PT)**: chain-of-custody and source credibility;
     broken down into source credentials, custody chain, and historical
     track record.
   - **Verification Strength (V)**: how strongly the record's authenticity
     can be technically verified (cryptographic signatures, audit trails,
     diversity of verification sources), distinct from Provenance Trust,
     which is about the chain of custody rather than the verification
     mechanism itself.
   - **Independent Confirmation (IC)**: whether the record is corroborated
     by a source independent of the one that produced it.
   - **Legal Compliance (L)**: GDPR and equivalent regulatory constraints
     on storing this specific record on an immutable, append-only ledger,
     including the right-to-erasure tension blockchain immutability
     creates. Distinct from the survey's Stage-1 legal/privacy gate (a
     hard pass/fail check applied before any of these six dimensions are
     even scored), which this survey does not ask you to weigh.
   - **Criticality (C)**: the operational or safety consequence if this
     record were lost, altered, or disputed later.
   - **Technical Feasibility Fit (F)**: how well the artefact fits ledger
     constraints (size, update rate, latency, cost). F = 1 - P.
   - **Economic Value (E)**: financial or asset value at stake if the data
     is corrupted or lost, including whether it could plausibly be
     tokenised or traded.
   - **Attack Resistance (A)**: difficulty of undetected manipulation,
     including the specific attack surface of Sybil, oracle, and insider
     attacks.

2. The top-level (L1: DVS, F, E, A) comparison is not interchangeable with
   the others: TrustRouter's composite combines these four
   multiplicatively (`TrustRouter = DVS x F x (1 + E) x A`), not as a
   weighted sum, so your L1 answer expresses relative importance among
   multiplicatively-combined factors, a different kind of judgement than
   every other level's "share of one linear total." See the concept-paper
   primer for the full explanation before answering L1.

3. Do not treat any one criterion as self-evidently more important than
   the others by default at any level. The purpose of this elicitation is
   to surface genuine professional disagreement about relative importance
   across different reviewers, human and agent alike. State your reasoning
   as if you expect it to be compared against differing judgements from
   other panel members, not as if there were an obviously correct ranking
   you are merely confirming.

4. Answer as the professional you are configured to be would, on the
   merits of these criteria as construction-project data-trust factors,
   not as an attempt to guess what the paper's authors want to hear (see
   the hypothesis document above: your answer is evidence for or against
   the paper's own claim, not a formality).

5. If you have been given reference material (the shared knowledge
   repository, a role-specific RAG corpus, or web search results), ground
   your Best/Worst choice and ratings in it and cite it by its exact tag,
   per the global rules. If you have not been given such material for a
   specific point, reason from your own domain expertise and say so
   plainly rather than implying you consulted a source you were not given.

6. Cite only real, verifiable, reputable sources: peer-reviewed papers,
   labelled preprints, standards documents (ISO, GDPR text, NIST, and
   similar), and academic or institutional technical reports. Never cite,
   or imply reliance on, a blog post, forum thread, marketing page, or any
   other source without real, checkable academic or institutional
   provenance. If you are not certain a source you are recalling from
   general knowledge meets this bar, say so explicitly rather than citing
   it as if it were verified.
