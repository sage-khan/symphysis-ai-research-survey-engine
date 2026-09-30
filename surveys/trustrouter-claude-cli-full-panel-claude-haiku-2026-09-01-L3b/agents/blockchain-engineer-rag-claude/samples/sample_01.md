# Sample 2 of 3

- Best: T_chain
- Worst: T_history

## Stated reasoning (submitted with the answer)

For a permissioned blockchain deployment storing construction-project records, custody chain integrity (T_chain) is the most critical provenance factor because: (1) it directly addresses the pre-blockchain risk that cannot be retrospectively fixed by on-chain storage—if data is altered before submission, blockchain immutability cannot restore authenticity; (2) for technical feasibility and tamper-evidence guarantees, establishing that data has not been modified in transit or storage is the prerequisite for anything else; (3) once on-chain, the ledger's cryptographic properties handle downstream integrity, but T_chain is the gating factor for storing valid data in the first place. T_source (source credentials and identity) is rated 3x less important than T_chain, not because identity is unimportant—it is essential for accountability—but in a permissioned system, source identity is pre-validated by network governance; the blockchain engineer's concern shifts to integrity of the data itself rather than identity verification, which is an access-control layer below blockchain deployment. T_history (historical track record) is rated 6x less important than T_chain because while a source's track record informs risk-based trust scoring (as noted in Rouhani and Deters 2021), it is not a technical prerequisite: a first-time or newer source can provide valid, unaltered data if T_source and T_chain are strong. Track record supports confidence judgment but does not determine technical feasibility. This assessment grounds in the engineering perspective: T_chain directly mitigates the attack surface for data integrity before ledger entry; T_source establishes accountability post-entry; T_history is a secondary risk-assessment factor.

## Sources cited

blockchain_trust_and_attack_resistance.md, shared knowledge: trustrouter_expert_questionnaire_v5_real_survey_instrument.md, general_knowledge (all claims verified genuine)
