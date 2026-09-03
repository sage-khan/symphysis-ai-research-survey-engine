# Sample 3 of 3

- Best: T_chain
- Worst: T_history

## Stated reasoning (submitted with the answer)

For a construction record being evaluated for blockchain storage, I ranked T_chain (custody chain integrity) as Best because it is the aspect blockchain technology most directly addresses: tamper-evidence of what happened to a record between creation and submission. In my day-to-day work federating multi-stakeholder models, the actual failure mode I see is not usually 'the author lacked credentials' but 'the file passed through several hands, exports, and re-imports and I can no longer be sure it wasn't altered or that the version I'm clash-detecting against is the approved one.' Custody-chain integrity is also the most directly and objectively verifiable of the three at the point of routing a specific record (was there a continuous, auditable handoff?), which matches the survey's stated goal of quantitative, automatic routing indicators. T_source (who authored it) is important as a baseline gate -- an unqualified or fraudulent author is a real risk -- but once credentials are established for a project role, that fact is largely static and doesn't vary record-by-record the way custody integrity does, so I placed it in the middle. T_history (the source's historical reliability) I ranked Worst: it's a useful prior/reputational signal, but it is the least direct evidence about the trustworthiness of any specific record under consideration -- a historically reliable party can still submit a compromised or mishandled file, and a less-established party can submit an impeccably documented one. I kept the ratios moderate (best-to-worst = 4) rather than extreme, because all three sub-parts of Provenance Trust are related and none is negligible; this is a real but not overwhelming difference in practical weight, and I want to be explicit that the source-vs-chain comparison in particular (rated 2) was a closer call than the chain-vs-history comparison.

## Sources cited

shared knowledge: trustrouter_expert_questionnaire_v5_real_survey_instrument.md, general_knowledge (all claims verified genuine)
