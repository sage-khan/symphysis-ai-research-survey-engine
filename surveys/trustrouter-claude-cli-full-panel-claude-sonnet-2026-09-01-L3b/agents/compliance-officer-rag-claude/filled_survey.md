# Filled survey: compliance-officer-rag-claude

- Agent ID: `compliance-officer-rag-claude`
- Role / expertise: Compliance and Regulatory Officer
- Model: claude_cli/sonnet
- DID: `did:key:z6Mkiny4nghtEZgRh1GDTK1uVN3K6yiWKovHursQ4YEVJq2c`
- RAG: enabled, corpus surveys/trustrouter-hawc-bwm/rag_corpora/compliance-officer
- Samples accepted: 3 (requested: 3 independent attempts)

## Summary

| Sample | Best | Worst |
|---|---|---|
| 0 | T_source | T_history |
| 1 | T_source | T_history |
| 2 | T_source | T_history |

## Sample 0

**Best:** T_source (Source credentials)  
**Worst:** T_history (Historical track record)

### Best-to-Others

| Criterion | Rating |
|---|---|
| T_source (Source credentials) | 1 |
| T_chain (Custody chain) | 2 |
| T_history (Historical track record) | 4 |

### Others-to-Worst

| Criterion | Rating |
|---|---|
| T_source (Source credentials) | 4 |
| T_chain (Custody chain) | 3 |
| T_history (Historical track record) | 1 |

### Reasoning

From a compliance-officer standpoint, T_source (source credentials) is the entry gate for legal validity: a construction record only carries regulatory weight if the person/organisation behind it had the authority to produce it (e.g. a chartered structural engineer's signed report, per the shared instrument's own example under PT). Without valid credentials, nothing downstream -- custody integrity or reliability history -- can rescue the record's legal standing, and this maps onto the same regulatory-identity concern the SoK on-chain-identity literature raises (on-chain identity as an AML/KYC-style compliance problem, gdpr_and_data_governance.md), where establishing who is behind a record is itself the compliance-critical step before any trust score is computed. T_chain (custody chain) is a close second: an unbroken, tamper-evident chain of custody from creation to submission is what lets a record stand up as evidence in a dispute or audit, and it is functionally what the accountability principle under GDPR and standard audit-trail practice both demand -- but it presupposes a credentialed source in the first place, so I rank it just below T_source rather than above or equal to it; this is a genuinely close call, not a wide gap. T_history (historical track record) is the weakest of the three from a strict compliance-gate perspective: it is a useful probabilistic/reputational signal for risk triage, but no building-code or GDPR obligation is gated on 'has this source been reliable before' -- a first-time submitter with impeccable credentials and an intact custody chain is fully compliant regardless of track record, whereas a source with a long good history but broken credentials or a tampered chain is not. Hence T_source best, T_history worst, with T_chain positioned closer to Best than to Worst.

## Sample 1

**Best:** T_source (Source credentials)  
**Worst:** T_history (Historical track record)

### Best-to-Others

| Criterion | Rating |
|---|---|
| T_source (Source credentials) | 1 |
| T_chain (Custody chain) | 3 |
| T_history (Historical track record) | 6 |

### Others-to-Worst

| Criterion | Rating |
|---|---|
| T_source (Source credentials) | 6 |
| T_chain (Custody chain) | 3 |
| T_history (Historical track record) | 1 |

### Reasoning

From a compliance officer's standpoint, Provenance Trust exists in the TrustRouter framework to answer 'who is accountable for this data and can that accountability be legally relied upon' -- and that question is answered first and most decisively by T_source. Source credentials (e.g., a signed report from a chartered structural engineer, per shared knowledge: trustrouter_expert_questionnaire_v5_real_survey_instrument.md's own worked example) establish the legal identity and authority of the data controller/author, which is the anchor point for GDPR accountability obligations and for construction-regulatory attribution of liability (who certified what, under what license). Without a credentialed, identifiable source, neither custody-chain evidence nor a track record has anyone to attach to -- an impeccable chain of custody for an anonymous or unlicensed source doesn't satisfy the regulatory need to know who is answerable for the record. T_chain (custody-chain integrity) is the second-most important: it is the evidentiary backbone for admissibility and tamper-evidence once a credentialed source is established, so I place it meaningfully but not overwhelmingly below T_source. T_history (historical track record) is the weakest of the three from a pure compliance lens: it is a reputational/probabilistic signal about past reliability, not a hard legal or regulatory requirement -- a first-time but properly licensed and credentialed source with an intact custody chain can be fully compliant even with no track record at all, whereas the reverse (a source with a long track record but no verifiable credentials or licensing) would still fail a legal/privacy suitability gate. This ordering reflects gdpr_and_data_governance.md's framing of establishing a privacy-compliant, accountable identity as the threshold regulatory concern that precedes any downstream trust scoring. I note this is a genuine judgement call rather than a source-documented ranking -- the reference material describes what T_source, T_chain, and T_history mean but does not itself rank them against each other, so the relative-importance ordering here is my own professional reasoning applied to those definitions.

## Sample 2

**Best:** T_source (Source credentials)  
**Worst:** T_history (Historical track record)

### Best-to-Others

| Criterion | Rating |
|---|---|
| T_source (Source credentials) | 1 |
| T_chain (Custody chain) | 2 |
| T_history (Historical track record) | 4 |

### Others-to-Worst

| Criterion | Rating |
|---|---|
| T_source (Source credentials) | 4 |
| T_chain (Custody chain) | 2 |
| T_history (Historical track record) | 1 |

### Reasoning

As the compliance officer accountable for tying a construction record back to a legally responsible party, T_source (credentials of the authoring person/organisation, per shared knowledge: trustrouter_expert_questionnaire_v5_real_survey_instrument.md's definition of PT decomposition) is the criterion that most directly satisfies regulatory and liability requirements: a signed dossier from a chartered structural engineer is meaningful precisely because the credential establishes who is legally answerable if the record is wrong, which is the same logic gdpr_and_data_governance.md applies when it frames on-chain identity as fundamentally an AML/KYC-style regulatory-compliance problem rather than a purely technical one. Without a credentialed source, an impeccable custody chain or a strong historical track record cannot manufacture legal accountability that isn't there. T_chain (custody-chain integrity from creation to submission) sits in the middle: it matters for tamper-evidence and audit admissibility, and complements T_source, but it presupposes a source worth tracking in the first place, so I rate it clearly below T_source but well above T_history. T_history (the source's past reliability) is the weakest for compliance purposes: it is a probabilistic, reputational signal that a new but properly credentialed and well-audited source may simply not have yet, and unlike credentials or a documented custody chain, a track record carries no binding legal weight on its own -- it is corroborative context, not a compliance requirement. I set best-to-others as T_source=1, T_chain=2, T_history=4, and others-to-worst as T_source=4, T_chain=2, T_history=1, which keeps the two tables consistent (2x2=4 matches the direct T_source-vs-T_history ratio of 4). This is a moderately close call between T_source and T_chain -- both are load-bearing for a compliance sign-off -- but T_history is clearly the weakest of the three on regulatory grounds.
