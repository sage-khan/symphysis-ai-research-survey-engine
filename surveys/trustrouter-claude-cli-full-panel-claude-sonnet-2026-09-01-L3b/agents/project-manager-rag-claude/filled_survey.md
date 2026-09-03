# Filled survey: project-manager-rag-claude

- Agent ID: `project-manager-rag-claude`
- Role / expertise: Construction Project Manager
- Model: claude_cli/sonnet
- DID: `did:key:z6MkmtkSj5oqsPgApLjX13QD1dY7KspgarWGkVzQin7EhVSk`
- RAG: enabled, corpus surveys/trustrouter-hawc-bwm/rag_corpora/project-manager
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
| T_history (Historical track record) | 5 |

### Others-to-Worst

| Criterion | Rating |
|---|---|
| T_source (Source credentials) | 5 |
| T_chain (Custody chain) | 3 |
| T_history (Historical track record) | 1 |

### Reasoning

As a construction PM deciding how much provenance trust to place in a record before it's committed to a ledger, the first and most load-bearing question is 'who actually produced this, and were they qualified to?' (T_source, per shared knowledge: trustrouter_expert_questionnaire_v5_real_survey_instrument.md's definition 'quality of authoring source (person/organisation)'). A structural calc or inspection sign-off from an unlicensed or unidentified party is untrustworthy no matter how clean its custody chain or how good that party's past record looks on other jobs -- credentials are the gating factor that everything else is conditional on, which is why I rank T_source as Best. T_chain (integrity of custody chain from creation to submission) is a close second, not a distant one: construction documents pass through many hands -- architect, GC, subcontractor, inspector -- and the Gartoumi 2024 scientometric review (construction_project_management_and_mcdm.md) specifically flags dispute resolution and document management as blockchain's strongest demonstrated use cases, precisely because an unverifiable chain-of-custody on a change order or sign-off is where disputes and cost overruns actually originate. So T_chain matters almost as much as T_source, hence only a 2 rather than a wide gap. T_history (has the source been reliable historically) is real signal but it is a lagging, aggregate indicator rather than something that validates this specific document: a newly licensed engineer or a new subcontractor may have excellent credentials and an impeccable custody trail on this record while having no track record at all, and conversely a generally reliable source can still submit a flawed or altered document on a given occasion. It is the most dispensable of the three for a document-level trust decision, so I set it as Worst. The 5 and 3 ratings reflect that gap being real but not extreme -- history is a legitimate corroborating factor, just the weakest of the three when the decision is about a specific piece of data.

## Sample 1

**Best:** T_source (Source credentials)  
**Worst:** T_history (Historical track record)

### Best-to-Others

| Criterion | Rating |
|---|---|
| T_source (Source credentials) | 1 |
| T_chain (Custody chain) | 2 |
| T_history (Historical track record) | 5 |

### Others-to-Worst

| Criterion | Rating |
|---|---|
| T_source (Source credentials) | 5 |
| T_chain (Custody chain) | 4 |
| T_history (Historical track record) | 1 |

### Reasoning

For a construction-project record being weighed for blockchain storage, T_source (who authored it -- a licensed structural engineer's stamped calculation vs. an unverified subcontractor's note) is the foundational trust determinant: it carries the legal and professional accountability that everything else depends on, and it's knowable at the moment the record is created, before any routing decision is even made. T_chain (custody-chain integrity from creation to submission) is the second most important: it answers whether a credentialed source's output was altered, substituted, or mishandled before it reached the ledger, which is precisely the tamper-evidence problem blockchain is meant to solve, per the dispute-resolution and document-management use cases documented in the Gartoumi 2024 review (construction_project_management_and_mcdm.md) where an unverifiable chain of custody on a change order or inspection sign-off creates the highest downstream cost. T_history (the source's track record) I rank lowest -- it's a useful but lagging, probabilistic signal: it can't be applied to a new but perfectly credentialed inspector or a first-time subcontractor, and a long track record doesn't retroactively fix a broken custody chain or a forged credential on a specific document. My ratings reflect a moderate gap between source and chain (2x) and a larger gap between source and history (5x), with source-to-history and chain-to-history calibrated consistently across both comparison directions. This is a judgement call from professional experience managing multi-party documentation flows, not drawn from a numeric weighting given in the reference material.

## Sample 2

**Best:** T_source (Source credentials)  
**Worst:** T_history (Historical track record)

### Best-to-Others

| Criterion | Rating |
|---|---|
| T_source (Source credentials) | 1 |
| T_chain (Custody chain) | 2 |
| T_history (Historical track record) | 6 |

### Others-to-Worst

| Criterion | Rating |
|---|---|
| T_source (Source credentials) | 6 |
| T_chain (Custody chain) | 3 |
| T_history (Historical track record) | 1 |

### Reasoning

For a construction PM deciding how a record should be routed (full on-chain / hybrid / conventional), Provenance Trust ultimately rests on being able to hold someone accountable for the data. T_source (source credentials) is the gatekeeping factor: a change order or inspection sign-off is only as trustworthy as the licensed engineer, inspector, or organization that stamped it, and that credential is verifiable at the moment of submission, independent of anything that happens afterward. T_chain (custody chain) matters next: even a credentialed source's record can be altered or substituted between creation and submission, and this is exactly the failure mode blockchain-style immutability is meant to close off, so it retains real weight but is secondary to knowing whether the originator was even qualified in the first place. T_history (historical track record) I rank lowest for this specific decomposition: many project-critical submissions come from newly engaged consultants, subcontractors, or one-off specialist inspectors with no accumulated track record on this project, so relying heavily on history would either be unavailable or would penalize legitimate new-but-credentialed sources. It is a useful corroborating signal but a lagging one, not a gate. The shared knowledge instrument (trustrouter_expert_questionnaire_v5_real_survey_instrument.md) defines these three sub-parts exactly as 'quality of authoring source,' 'integrity of custody chain,' and 'historical track record,' which is the framing I applied; construction_project_management_and_mcdm.md's point about dispute-resolution scenarios (an under-documented change order or inspection sign-off creating the highest downstream cost if trust can't later be established) reinforced why the originating credential and the intactness of custody -- not accumulated history -- are what actually gets tested when a dispute arises. This is a judgement call rather than something the literature directly ranks, and I flag that the T_source vs T_chain gap is the closer call of the three; T_history trailing both was the clearer distinction.
