# Sample 2 of 3

- Best: A_insider
- Worst: A_sybil

## Stated reasoning (submitted with the answer)

For construction-project records under consideration for blockchain storage, the realistic attacker profile matters more than the theoretical one. Construction data ecosystems (owners, contractors, inspectors, insurers, authorities) are almost always run as permissioned/consortium networks with vetted, credentialed participants rather than open public networks -- so Sybil resistance (defending against fake anonymous identities flooding the system) addresses a threat model that is largely already mitigated by the permissioned onboarding process itself (KYC-style vetting of contractors, licensed engineers, registered authorities). That makes A_sybil the weakest link of the three for this domain. Insider resistance (A_insider), by contrast, targets the attack vector most documented in construction-fraud cases: a party with legitimate, already-vetted credentials -- an inspector, subcontractor, or project manager -- falsifying test results, inspection sign-offs, or compliance records. Because virtually every category of construction documentation (structural, energy, compliance) is created or approved by credentialed insiders, this is the most pervasive and consequential threat surface, and is the primary reason such records draw institutional and insurer scrutiny over decades. Oracle resistance (A_oracle) sits in between: it matters greatly for sensor/IoT-fed data (structural health monitoring, energy metering) but is narrower in scope than insider resistance because a large share of construction documentation is manually authored/approved rather than sensor-derived, so oracle tampering cannot corrupt every record category the way insider abuse can. This ordering (A_insider > A_oracle > A_sybil) reflects my professional judgement of realistic threat prevalence and consequence in multi-decade, multi-stakeholder construction documentation, not a claim from the reference material, which defines the three sub-parts but does not itself rank them.

## Sources cited

shared knowledge: trustrouter_expert_questionnaire_v5_real_survey_instrument.md, general_knowledge (all claims verified genuine)
