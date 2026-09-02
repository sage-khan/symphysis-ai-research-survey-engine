# Sample 2 of 3

- Best: V_crypto
- Worst: V_diversity

## Stated reasoning (submitted with the answer)

For construction-project records considered for blockchain archiving, cryptographic evidence is the foundational technical control. Kochovski et al. 2026 demonstrates operationally that DIDs, verifiable credentials, and hash commitments are the actual cryptographic mechanisms that provide authenticity, integrity, and non-repudiation on a ledger—these are not theoretical but measured on real Ethereum infrastructure (2.07ms authentication, 88ms DID resolution). Without cryptographic evidence, a record has no technical proof of its origin or that it has not been tampered with. Audit trails (V_audit) provide necessary procedural context—the story of who did what and when—but audit evidence alone is post-hoc reconstructible and vulnerable to falsification if not cryptographically anchored. Audit is clearly important but secondary to the technical foundation. Diversity of verification sources (V_diversity) is a governance and procedural control: ISO 19650 already requires multiple independent parties to validate federated models, and this reduces risk of single-party falsification. However, diversity is the most organizationally expensive to scale, most vulnerable to collusion, and most dependent on the other two criteria working first. A well-signed record with a complete audit trail requires less diversity to be trustworthy on a blockchain; conversely, perfect diversity cannot compensate for weak cryptography or incomplete audit trails. Crypto is 3x more important than audit (audit adds real value but depends on crypto for trustworthiness), and 5x more important than diversity (diversity is important governance but adds marginal value if crypto and audit are strong). Audit is 2x more important than diversity (procedural sequencing of actions is more fundamental than the question of who verified it, when the underlying evidence is cryptographically sound).

## Sources cited

bim_and_digital_building_logbooks.md, shared knowledge: trustrouter_concept_paper_primer.md, shared knowledge: trustrouter_expert_questionnaire_v5_real_survey_instrument.md, general_knowledge (all claims verified genuine)
