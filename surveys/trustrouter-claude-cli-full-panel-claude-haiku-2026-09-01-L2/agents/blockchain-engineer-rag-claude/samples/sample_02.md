# Sample 3 of 3

- Best: V
- Worst: L

## Stated reasoning (submitted with the answer)

Verification Strength (V) is the best criterion for construction-data routing decisions because it is the unique technical capability that blockchain (especially permissioned ledgers like Hyperledger Fabric) actually provides: cryptographic proof of authenticity, immutable audit trails, and provable absence of tampering. In real deployments, V is the mechanism that determines what level of consensus a transaction requires—as Rouhani & Deters (2021) show, adaptive transaction validation directly adjusts signature requirements based on the computed trust value, meaning V is the control lever for the routing decision itself. For construction records where liability and evidence preservation matter, the ability to prove a record is authentic and unaltered (V) is more foundational than trust in the data source alone (PT) or data quality (Q), both of which are necessary but insufficient without cryptographic proof. Q and PT establish baseline credibility; V is what blockchain adds. IC (independent confirmation) is close to V in value but requires external coordination that may not always be available. C (criticality) drives *requirements* for V but V is the *mechanism*. Legal Compliance (L) is worst because it is not a trust dimension itself but an external gate or constraint. L determines whether on-chain storage is *permitted*, not whether data is *trustworthy*; a record can have high Q, PT, V, IC, and C but still be excluded by L (e.g., GDPR right to be forgotten vs. blockchain's immutability). In the routing decision, L acts as a binary admissibility filter applied *after* trust assessment, whereas the other five dimensions directly measure data trustworthiness. For a permissioned ledger where you control participants and endorsement policies, V is what you control and leverage; L is what constrains you externally.

## Sources cited

shared knowledge: trustrouter_expert_questionnaire_v5_real_survey_instrument.md, blockchain_trust_and_attack_resistance.md, general_knowledge (all claims verified genuine)
