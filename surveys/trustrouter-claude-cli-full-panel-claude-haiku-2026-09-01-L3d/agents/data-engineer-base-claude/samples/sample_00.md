# Sample 1 of 3

- Best: A_oracle
- Worst: A_sybil

## Stated reasoning (submitted with the answer)

Construction-project data is fundamentally empirical, depending on physical sensors and devices (load cells, inclinometers, concrete testers, GPS, progress cameras, structural monitoring) for factual record-keeping. Oracle resistance—the ability to prevent sensor and device tampering—directly protects the integrity of the raw data being routed. Compromised sensor data corrupts the foundation of all downstream decisions and routing choices, regardless of where data is stored or what cryptographic protections wrap it. This is my strongest ranking factor.

Insider resistance ranks second. In construction, many legitimate users have system access (site engineers, project managers, inspectors, facility managers). A malicious insider with real credentials can directly alter data, manipulate routing logic, or corrupt provenance records within systems designed with audit trails. While insider threats are serious, they operate within systems that typically maintain transaction logs and custodial records; the damage is constrained by what can be hidden. Oracle attacks, by contrast, inject false data at the source before it enters any system.

Sybil resistance ranks lowest. While fake-identity attacks matter for governance and access control, construction projects operate within regulated credential ecosystems (PE licenses, CEng, contractor licensing, insurance bonds, organizational hierarchies). Creating and maintaining multiple fraudulent professional identities in construction is substantially harder than in purely digital systems. Even with some Sybil presence, established organizations with verified credentials can provide trustworthy data anchors. Sybil threats primarily affect voting weight and governance, not the core factual integrity of sensor-derived construction records. In the context of routing decisions between on-chain and conventional storage, Sybil attacks are less direct threats to data quality than the other two.

The best-to-insider rating of 2 reflects that both are serious, but oracle attacks are more foundational. The best-to-sybil rating of 4 reflects the larger gap between protecting source data integrity and managing identity spoofing in a licensed industry. The insider-to-sybil rating of 2 reflects that insiders with real access pose more direct threats than multiple fake identities in construction's credential-heavy environment.

## Sources cited

shared knowledge: trustrouter_expert_questionnaire_v5_real_survey_instrument.md, general_knowledge (all claims verified genuine)
