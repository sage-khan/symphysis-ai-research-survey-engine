# Sample 1 of 3

- Best: A_insider
- Worst: A_sybil

## Stated reasoning (submitted with the answer)

In permissioned-ledger construction deployments, attack-resistance priorities differ from public blockchains. A_insider (malicious legitimate access) is the most consequential threat because: (1) identity enrollment and permissioning inherently mitigate sybil attacks—construction projects involve known, vetted organizations, so creating multiple false identities is blocked at the access layer; (2) insider threats cannot be prevented by the ledger's permissioning alone—a trusted contractor, inspector, or engineer with legitimate credentials can record falsified data (incorrect measurements, material certifications, or structural assessments) that appears valid on-chain; (3) detection of insider fraud requires cryptographic audit trails, peer-verification procedures, and segregation of duties rather than technical identity controls. A_oracle (sensor and device tampering) ranks second: physical sensors and measurement devices can be compromised, requiring tamper-evidence mechanisms and cryptographic signatures on sensor feeds. However, in permissioned construction contexts, oracle risks are partially mitigated through known-device enrollment and procedural verification (re-testing by independent parties). A_sybil is least important because the permissioning layer itself solves the core problem—identity is managed through enrollment certificates and access control, not consensus-based reputation. Sybil attacks are primarily a public-blockchain threat; permissioned ledgers eliminate this vector by design. The 8:4:1 ratio reflects that insider threats are roughly twice as hard to mitigate as oracle threats, and both are substantially more consequential than sybil resistance in this deployment context.

## Sources cited

shared knowledge: trustrouter_expert_questionnaire_v5_real_survey_instrument.md, general_knowledge (all claims verified genuine)
