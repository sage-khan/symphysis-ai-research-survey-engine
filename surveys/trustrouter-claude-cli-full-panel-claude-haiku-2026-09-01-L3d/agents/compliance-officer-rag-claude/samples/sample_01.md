# Sample 2 of 3

- Best: A_insider
- Worst: A_sybil

## Stated reasoning (submitted with the answer)

From a facility-management compliance officer's perspective, insider resistance is the most critical attack vector for construction records destined for blockchain storage. Insiders with legitimate credentials bypass most technical gatekeeping and can directly falsify safety certifications, compliance attestations, and regulatory records—creating non-repudiable audit trails of fraudulent data that later become immutable. GDPR compounds this: an insider can mishandle personal data embedded in construction records (workforce safety records, biometric access logs) under the cover of legitimate access. Oracle resistance (device/sensor tampering) is significant but operationally more tractable—physical devices have fewer attack surface points than the human authorization layer, redundancy and cryptographic verification can mitigate compromise, and sensor anomalies often create observable physical inconsistencies that trigger investigation. Sybil resistance, by contrast, is the most preventable: construction-sector actors already undergo identity verification and credentialing during onboarding (trade licenses, professional certifications, contractor vetting); once legitimate identity is established, creating and operating multiple false personas requires sustained social engineering or document fraud, both rarer than insider exploitation of existing legitimate access. In regulatory terms, sybil attacks exploit the front gate; insider attacks exploit the entire perimeter once inside. I rate A_insider 8× more important than A_sybil because the attack surface and deniability are fundamentally asymmetric. A_insider vs A_oracle is rated 7× because insider threats are harder to detect and prevent through technical means alone, whereas oracle tampering leaves traces in comparative data sources and device logs. A_oracle is rated 5× more important than A_sybil because device integrity failures can silently corrupt data at collection time (before blockchain entry), whereas sybil mitigation relies on well-established identity controls already in use.

## Sources cited

gdpr_and_data_governance.md, shared knowledge: trustrouter_expert_questionnaire_v5_real_survey_instrument.md, general_knowledge (all claims verified genuine)
