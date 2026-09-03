# Sample 1 of 3

- Best: T_source
- Worst: T_history

## Stated reasoning (submitted with the answer)

From a compliance-officer standpoint, T_source (source credentials) is the entry gate for legal validity: a construction record only carries regulatory weight if the person/organisation behind it had the authority to produce it (e.g. a chartered structural engineer's signed report, per the shared instrument's own example under PT). Without valid credentials, nothing downstream -- custody integrity or reliability history -- can rescue the record's legal standing, and this maps onto the same regulatory-identity concern the SoK on-chain-identity literature raises (on-chain identity as an AML/KYC-style compliance problem, gdpr_and_data_governance.md), where establishing who is behind a record is itself the compliance-critical step before any trust score is computed. T_chain (custody chain) is a close second: an unbroken, tamper-evident chain of custody from creation to submission is what lets a record stand up as evidence in a dispute or audit, and it is functionally what the accountability principle under GDPR and standard audit-trail practice both demand -- but it presupposes a credentialed source in the first place, so I rank it just below T_source rather than above or equal to it; this is a genuinely close call, not a wide gap. T_history (historical track record) is the weakest of the three from a strict compliance-gate perspective: it is a useful probabilistic/reputational signal for risk triage, but no building-code or GDPR obligation is gated on 'has this source been reliable before' -- a first-time submitter with impeccable credentials and an intact custody chain is fully compliant regardless of track record, whereas a source with a long good history but broken credentials or a tampered chain is not. Hence T_source best, T_history worst, with T_chain positioned closer to Best than to Worst.

## Sources cited

shared knowledge: trustrouter_expert_questionnaire_v5_real_survey_instrument.md, gdpr_and_data_governance.md, general_knowledge (all claims verified genuine)
