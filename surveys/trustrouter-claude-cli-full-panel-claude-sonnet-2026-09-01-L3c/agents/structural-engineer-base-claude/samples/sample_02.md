# Sample 3 of 3

- Best: V_diversity
- Worst: V_crypto

## Stated reasoning (submitted with the answer)

For a structural-capacity dossier relied on by insurers, regulators and owners over decades, the substantive question is whether the recorded fact (e.g. a load capacity finding, an inspection result) is actually correct and can be trusted independently of any one party. Diversity of verification sources (V_diversity) most directly answers that: it is the digital analogue of the independent-checking-engineer principle already embedded in structural practice (e.g. category 3/independent design checks) -- a second, unrelated party confirming the same finding is the strongest defence against both honest error and deliberate misrepresentation, and it is the hardest property to fake because it requires collusion across multiple independent actors rather than compromise of a single system or credential. Audit-trail completeness (V_audit) is necessary supporting infrastructure -- it lets you reconstruct who did what and when, which matters for liability tracing and for detecting anomalies in the process -- but by itself it only documents a single chain of custody; a complete and clean audit trail can still record a single mistaken or biased assessment with no external corroboration. Cryptographic evidence (V_crypto) I rank lowest of the three: it is valuable for tamper-evidence and non-repudiation of a signed record over the long custody periods involved, but a valid signature or hash only proves the record has not been altered since signing -- it says nothing about whether the underlying engineering judgement or data was correct in the first place, and a single cryptographically signed but never independently corroborated report is exactly the single-point-of-failure scenario that concerns long-term reliance by third parties. The ratios reflect a genuine but not extreme spread: this was a closer call between V_audit and V_diversity than between either of those and V_crypto, since audit trails do meaningfully support accountability, but I judged independent corroboration as the more decisive verification property for structural-safety-critical data.

## Sources cited

shared knowledge: trustrouter_expert_questionnaire_v5_real_survey_instrument.md, general_knowledge (all claims verified genuine)
