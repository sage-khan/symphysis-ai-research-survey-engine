# Sample 2 of 3

- Best: A_oracle
- Worst: A_insider

## Stated reasoning (submitted with the answer)

For construction-project records routed to blockchain, oracle resistance is the most decisive technical factor. Construction data authenticity depends critically on trustworthy sensor and device input—structural monitoring (beam deflection, concrete strength), environmental conditions (temperature, humidity), and site measurements feed directly into compliance records. As Adler et al. (2018, Astraea) frames it, the oracle problem is fundamental: smart contracts can only act on on-chain data, so they require a trusted mechanism to attest real-world facts (sensor readings, off-chain events) before that data can be used on-chain. If sensors or their data feeds can be tampered with or spoofed, the entire construction record loses integrity at the source level—no downstream validation recovers this. This attack surface is the least mitigated by existing non-blockchain mechanisms.

A_sybil is substantively less critical for construction. Vaziry et al. (2024) identifies Sybil as the digital-physical identity mapping problem: trusting that an on-chain identity truly represents the real contractor, inspector, or certifying engineer. However, construction already operates within established regulatory frameworks (PE/CEng credentials, bonding, licensing). Sybil resistance at the on-chain layer adds protection, but the attack is partially pre-filtered by the identity-issuance process. Sybil resistance remains important (rated 5x less critical than oracle) but it is not the limiting factor in construction data trust.

A_insider resistance is least important technically. Vaziry et al. also addresses this as trusting the identity issuers and the legitimately credentialed actors who vouch for or submit records. An insider attack—a credentialed engineer or inspector acting maliciously—is the hardest to prevent at the technical layer alone. No perfect cryptographic solution exists: once access is legitimately granted, detecting and preventing abuse requires monitoring, role separation, and behavioral flags. Construction partially delegates insider control to existing contractual, insurance, and professional-liability mechanisms (bonds, E&O insurance, disciplinary boards). While insider resistance matters, it is less of a distinctive blockchain technical problem and more of a governance/monitoring problem that transcends the ledger layer.

## Sources cited

blockchain_trust_and_attack_resistance.md, shared knowledge: trustrouter_expert_questionnaire_v5_real_survey_instrument.md, general_knowledge (all claims verified genuine)
