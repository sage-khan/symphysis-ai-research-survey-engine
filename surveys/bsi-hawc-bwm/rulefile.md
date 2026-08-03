# Survey rules: BSI Stage-2 Dimension Weight Elicitation (HAWC-BWM)

This survey elicits Best-Worst Method weights over six TrustRouter/Blockchain
Suitability Index (BSI) dimensions: Quality (Q), Provenance Trust (PT),
Verification Strength (V), Independent Confirmation (IC), Legal Compliance
(L), and Criticality (C). Your Best/Worst judgement determines how heavily
each dimension counts when TrustRouter decides whether a piece of
construction-project data belongs on a blockchain or in a conventional
database. These rules apply in addition to the global rules; they exist to
keep every agent's judgement grounded in this specific framework, not a
generic notion of "data trust."

1. These six dimensions are deliberately not interchangeable with generic
   data-quality criteria from another domain. Ground every comparison in
   what each dimension specifically means for a construction-project
   record considered for blockchain storage:
   - **Quality (Q)**: completeness, accuracy, and timeliness of the record
     itself.
   - **Provenance Trust (PT)**: chain-of-custody and source credibility,
     who asserted this record and through what chain of custody.
   - **Verification Strength (V)**: how strongly the record's authenticity
     can be technically verified (cryptographic signatures, sensor
     attestation, and similar mechanisms), distinct from Provenance Trust,
     which is about the chain of custody rather than the verification
     mechanism itself.
   - **Independent Confirmation (IC)**: whether the record is corroborated
     by a source independent of the one that produced it, distinct from
     Verification Strength, which concerns the mechanism, not independence
     of the confirming party.
   - **Legal Compliance (L)**: GDPR and equivalent regulatory constraints
     on storing this specific record on an immutable, append-only ledger,
     including the right-to-erasure tension that a blockchain's
     immutability creates.
   - **Criticality (C)**: the operational or safety consequence if this
     record were lost, altered, or disputed later, for example in a
     liability dispute or a structural failure investigation.

2. Do not treat any one dimension as self-evidently more important than
   the others by default. The whole purpose of this elicitation is to
   surface genuine professional disagreement about their relative
   importance across different reviewers, human and agent alike. State
   your reasoning as if you expect it to be compared against differing
   judgements from other panel members, not as if there were an obviously
   correct ranking you are merely confirming.

3. This survey's result is combined with a real human expert panel's
   responses (see this survey's `weighting.human_responses_path` and the
   HAWC-BWM alpha sensitivity sweep). Your answer is one input to that
   combined result, not a stand-in for the human panel and not something
   that should defer to an assumed human consensus. Answer as the
   professional you are configured to be would, on the merits of these
   six dimensions as construction-project data-trust criteria.

4. If you have been given reference material specific to TrustRouter, the
   Blockchain Suitability Index, or construction-industry data governance,
   ground your Best/Worst choice and ratings in it and cite it by its
   exact tag, per the global rules. If you have not been given such
   material, reason from your own domain expertise and say so plainly
   rather than implying you consulted a source you were not given.
