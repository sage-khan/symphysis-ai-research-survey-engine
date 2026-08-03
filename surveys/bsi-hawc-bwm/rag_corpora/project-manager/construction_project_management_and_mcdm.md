# Construction project management, blockchain adoption, and multi-criteria decision-making

Real, catalogued sources relevant to Legal Compliance (L), Criticality
(C), and the general multi-criteria weighting approach this survey itself
uses (BWM). Drawn from `docs/research/LITERATURE_REVIEW_CATALOG.csv` in
the project-veritas literature bank.

## Five-Year Review of Blockchain in Construction Management: Scientometric and Thematic Analysis (2017-2023), Gartoumi, 2024 (Automation in Construction, 168:105773)

Scientometric and thematic analysis of 237 documents on blockchain in
construction management (2017-2023), identifying eight application
categories and noting blockchain's demonstrated benefits in dispute
resolution, document management, and BIM efficiency. Relevant to how a
construction project manager should weigh Criticality (C): the review's
dispute-resolution use cases are exactly the scenario where an
under-documented or unverifiable data item (a change order, an inspection
sign-off) creates the highest downstream cost if its trust cannot later
be established.

## Multi-Attribute Decision Making-based Trust Score Calculation in Trust Management in IoT, Bampatsikos, Politis, Bolgouras, and Xenakis, 2023 (ACM ARES 2023, DOI:10.1145/3600160.3605074)

Proposes a Multi-Attribute Decision Making (MADM) methodology for
computing IoT device trust scores that update dynamically over a device's
lifetime, rather than the oversimplified static models common in prior
work. Notably, under its "high-cybersecurity-risk" mode, the MADM-weighted
score is overridden entirely once a device's cyber-risk crosses a
threshold, functioning as a hard gate on top of a weighted score, exactly
the two-stage constraint-gate-then-weighted-scoring architecture this
survey's own concept paper (see the shared knowledge_repo primer) uses.
Useful precedent for why TrustRouter's gates are unconditional rather than
one more criterion averaged into the trust score.

## Ordinal Priority Approach (OPA) in Multiple Attribute Decision-Making, Ataei, Mahmoudi, Feylizadeh, and Li, 2020 (Applied Soft Computing 86, Elsevier)

Introduces OPA, a multi-attribute decision-making method that, like BWM,
uses expert preference information (in OPA's case, purely ordinal
rankings) and a linear-programming formulation, rather than the full
pairwise comparison matrix AHP requires. Useful comparative context for
why this survey uses BWM specifically (fewer, more reliable pairwise
judgments than AHP, per Rezaei's original 2015 motivation) rather than a
full pairwise or purely ordinal method: BWM sits between OPA's minimal
ordinal input and AHP's exhaustive pairwise matrix in terms of
elicitation burden versus statistical power.
