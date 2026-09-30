# Sample 1 of 3

- Best: V_crypto
- Worst: V_diversity

## Stated reasoning (submitted with the answer)

Verification Strength (V) at L2 is about the technical robustness of the evidence that a record is what it claims to be ('signatures / logs' per the survey instrument's own gloss). Of the three sub-parts, V_crypto (signatures, hashes, PKI) is the most direct and objective embodiment of that: it is what actually makes a construction record tamper-evident and non-repudiable, and it is the mechanism the concept-paper primer lists first under V and that underlies the SHA-256 commitment example in the survey's own IoT vibration-stream vignette. I rated it Best. V_audit (who-did-what-when logging/lineage) is a close second rather than a distant one -- the data_quality_and_polyglot_persistence.md note that 'a data pipeline's own audit logging and lineage tracking is often the first-hand source of evidence a Verification Strength (V) ... score should actually be based on' means audit trails are frequently the operational substrate crypto evidence gets attached to, so I only rated V_crypto twice as important as V_audit, not more -- this is a genuinely close call. V_diversity (multiple independent verifying parties) I rated Worst: from a data-engineering standpoint, breadth of independent corroboration is real and useful, but it substantially overlaps in function with the separate top-level Independent Confirmation (IC) factor described in the concept-paper primer, making it comparatively less load-bearing specifically within the Verification-Strength construct, whereas crypto and audit evidence are the properties actually intrinsic to a given record's own trustworthiness. This is a judgement call about factor boundaries (V vs. IC) rather than a claim drawn directly from the reference material.

## Sources cited

data_quality_and_polyglot_persistence.md, shared knowledge: trustrouter_concept_paper_primer.md, shared knowledge: trustrouter_expert_questionnaire_v5_real_survey_instrument.md, general_knowledge (all claims verified genuine)
