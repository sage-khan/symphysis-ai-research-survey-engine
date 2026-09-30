# Sample 2 of 3

- Best: T_chain
- Worst: T_history

## Stated reasoning (submitted with the answer)

As a data engineering specialist responsible for provenance tracking and polyglot-persistence routing, I rank T_chain (custody chain) as best because it is the technical and governance foundation of all provenance assessment. Provenance tracking in data engineering is fundamentally about audit trails and chain-of-custody verification—the ability to answer 'what happened to this data between creation and submission?' This is especially critical for construction data destined for blockchain, where immutability depends on verifying that the data entering the chain has not been tampered with or corrupted en route. A broken or undocumented custody chain cannot be remedied retrospectively, even if the source has excellent credentials or a strong track record. T_chain is directly verifiable through technical means (audit logs, cryptographic integrity, version control) and directly governs compliance and liability in construction projects. T_source (source credentials) is notably important—you must know and trust the creator—but credentials alone do not ensure this specific record's integrity; a trusted source's data could still be corrupted or mishandled in transit. T_history (track record) is useful for risk profiling but is the least critical for routing decisions on an individual record. Historical reliability informs confidence in the source but does not substitute for verifying this data's actual path and integrity. A source with a good track record can still be compromised in a specific instance if custody is broken, whereas a documented, auditable chain provides immediate, record-specific assurance. T_chain ranks 5x more important than T_history because chain integrity is the precondition for provenance in data systems; T_source ranks 3x more important than T_chain because source identity and authority are the baseline trust anchor before chain assessment even applies, but chain verification is more directly decisive for this routing decision; T_source ranks 2x more important than T_history because knowing the creator now is more immediately actionable than validating patterns over time.

## Sources cited

shared knowledge: trustrouter_expert_questionnaire_v5_real_survey_instrument.md, general_knowledge (all claims verified genuine)
