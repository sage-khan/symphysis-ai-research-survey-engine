# Filled survey: bim-coordinator-rag-claude

- Agent ID: `bim-coordinator-rag-claude`
- Role / expertise: BIM Coordinator
- Model: claude_cli/sonnet
- DID: `did:key:z6MkqSfDfSA3Y6V2HcU6A72f4t469gxYRVPTADrJ7HzYtu7a`
- RAG: enabled, corpus surveys/trustrouter-hawc-bwm/rag_corpora/bim-coordinator
- Samples accepted: 3 (requested: 3 independent attempts)

## Summary

| Sample | Best | Worst |
|---|---|---|
| 0 | IQ | RQ |
| 1 | IQ | RQ |
| 2 | IQ | RQ |

## Sample 0

**Best:** IQ (Intrinsic Quality)  
**Worst:** RQ (Representational Quality)

### Best-to-Others

| Criterion | Rating |
|---|---|
| IQ (Intrinsic Quality) | 1 |
| CQ (Contextual Quality) | 3 |
| RQ (Representational Quality) | 5 |

### Others-to-Worst

| Criterion | Rating |
|---|---|
| IQ (Intrinsic Quality) | 5 |
| CQ (Contextual Quality) | 3 |
| RQ (Representational Quality) | 1 |

### Reasoning

As BIM coordinator responsible for federating models from multiple stakeholders and signing off on data before it moves into long-term (potentially blockchain) storage, my first gate is always: are the values themselves correct? Intrinsic Quality (IQ) bundles accuracy, validity, and uniqueness -- if a room dimension, a material spec, or an inspection reading is simply wrong, duplicated, or invalid at the point of capture, nothing downstream (scope completeness, timeliness, or cross-copy consistency) can fix that; per shared knowledge: trustrouter_expert_questionnaire_v5_real_survey_instrument.md, IQ is explicitly framed as 'are the values right in themselves?', which is the precondition for everything else. Contextual Quality (CQ, completeness+timeliness) matters a great deal in practice -- a federated model missing a discipline's submission or built on stale MEP data causes real clash-detection failures -- so I rate it meaningfully behind IQ but well ahead of RQ, not negligible (best_to_others CQ=3). Representational Quality (RQ, consistency across copies/sources) is the one I rank lowest: in an ISO 19650-governed federation workflow, format/version alignment across federated copies is substantially a process-and-tooling problem (common data environment discipline, naming/versioning conventions) that is easier to detect and remediate mechanically once IQ and CQ are in order -- per bim_and_digital_building_logbooks.md's discussion of ISO 19650 requiring independent validation of federated models before acceptance, consistency issues surface at that federation checkpoint rather than being an intrinsic property of the record's truth-value. This is a judgement call from my own domain experience, not something the reference material states outright, and I acknowledge CQ vs RQ is a clearer gap than IQ vs CQ, which is the closer call of the three.

## Sample 1

**Best:** IQ (Intrinsic Quality)  
**Worst:** RQ (Representational Quality)

### Best-to-Others

| Criterion | Rating |
|---|---|
| IQ (Intrinsic Quality) | 1 |
| CQ (Contextual Quality) | 3 |
| RQ (Representational Quality) | 5 |

### Others-to-Worst

| Criterion | Rating |
|---|---|
| IQ (Intrinsic Quality) | 5 |
| CQ (Contextual Quality) | 3 |
| RQ (Representational Quality) | 1 |

### Reasoning

As a BIM coordinator, I judge Intrinsic Quality (accuracy, validity, uniqueness) to be the bedrock of a trustworthy record. If the underlying values are wrong -- a mis-measured dimension, an invalid material classification, a duplicated/contradictory element record -- then anchoring that record on an immutable ledger just permanently enshrines an error; no amount of completeness, timeliness, or cross-copy consistency can compensate for data that is factually wrong at the source. This matches how ISO 19650-style information management treats validation of federated models before acceptance (per bim_and_digital_building_logbooks.md's discussion of independent validation of federated models) -- correctness of the underlying content is checked before the model is trusted, not after. Contextual Quality (completeness/timeliness) sits in the middle: a partial or slightly stale record is a real problem for lifecycle documentation, but it is a fitness-for-use gap that can often be remedied incrementally (supplementary entries, versioned updates) without undermining what has already been recorded. Representational Quality (consistency across sources/copies) is important in a federated, multi-stakeholder BIM environment -- disagreeing copies genuinely complicate clash detection and audit trails -- but it is the narrowest of the three (a single facet, consistency, versus IQ's three facets or CQ's two), and it is logically downstream of IQ: consistency between multiple copies of inaccurate data does not make the data trustworthy, it just makes the error uniform. That is why I rank RQ as least important of the three quality clusters here, while acknowledging the comparison between CQ and RQ was closer than IQ's clear lead -- both are legitimate secondary concerns that federated-model coordination cares about daily. I did not find material in the provided ISO 25012 cluster definitions (shared knowledge: trustrouter_expert_questionnaire_v5_real_survey_instrument.md, shared knowledge: trustrouter_concept_paper_primer.md) or the BIM-domain reference material that dictates a specific ranking among IQ/CQ/RQ, so this ordering reflects my own professional judgement as a BIM coordinator applied to those cluster definitions, not a value taken directly from a source.

## Sample 2

**Best:** IQ (Intrinsic Quality)  
**Worst:** RQ (Representational Quality)

### Best-to-Others

| Criterion | Rating |
|---|---|
| IQ (Intrinsic Quality) | 1 |
| CQ (Contextual Quality) | 3 |
| RQ (Representational Quality) | 5 |

### Others-to-Worst

| Criterion | Rating |
|---|---|
| IQ (Intrinsic Quality) | 5 |
| CQ (Contextual Quality) | 3 |
| RQ (Representational Quality) | 1 |

### Reasoning

As the BIM coordinator running clash detection and lifecycle documentation across federated models, my first filter on any record is whether the values themselves are correct: accuracy, validity against schema/domain rules, and uniqueness (no duplicate/conflicting element records) are what determine whether a model element can be trusted at all before it's even used in a decision. This is IQ (shared knowledge: trustrouter_expert_questionnaire_v5_real_survey_instrument.md and trustrouter_concept_paper_primer.md define IQ as accuracy/validity/uniqueness). If IQ fails, nothing downstream matters - a wrong dimension or duplicated asset ID corrupts every clash check and every compliance record regardless of when it arrived or how well it matches other copies. CQ (completeness, timeliness) matters a great deal in practice - an incomplete as-built or a stale inspection record is a real operational problem I deal with constantly during handover and federation - but a complete, timely record that is inaccurate is arguably worse than a partial but correct one, so I place CQ second. RQ (consistency across sources/copies) is the criterion I rate lowest of the three: cross-copy consistency is exactly what ISO 19650-style federation and independent validation by multiple task teams (bim_and_digital_building_logbooks.md, discussing BS EN ISO 19650 Guidance Part 2) is designed to catch and reconcile after the fact - it's a synchronization/version-control problem that tooling and process controls (federation checks, common data environment version control) address reasonably well, whereas inaccurate underlying data or timeliness gaps are harder to detect and more consequential once they propagate into a blockchain-anchored record that is meant to be immutable. This is a judgement call based on my practical experience with federated model governance, not a hard finding from the reference material, and I want to flag that IQ vs CQ is a real trade-off - a project with severe completeness gaps (e.g., missing structural inspection records for a hospital renovation) could plausibly be argued as equally urgent as accuracy problems. I did not find material in the provided sources that quantifies this trade-off numerically, so my ratings (IQ:CQ:RQ = 5:3:1 relative to worst) reflect professional judgement about which failure mode is most damaging to an immutable, blockchain-anchored construction record.
