# Sample 2 of 3

- Best: IQ
- Worst: CQ

## Stated reasoning (submitted with the answer)

IQ (accuracy, validity, uniqueness) is the foundational gate for a construction-project record before it is ever considered for blockchain storage: if the underlying values are wrong, invalid, or duplicated, no amount of completeness, timeliness, or cross-source agreement can compensate, and worse, an inaccurate value written to an immutable ledger becomes a permanent, unfixable trust liability -- this is the classic 'garbage in, garbage immutably out' risk that a data engineer has to gate against upstream of any routing decision. RQ (consistency across sources) is the second most important cluster from this role's specific vantage point: per data_quality_and_polyglot_persistence.md's discussion of polyglot persistence (Prasad and S B 2014; Kosmerl, Rabuzin and Sestak 2018), a construction dataset routed across specialized stores (time-series, relational, graph, and now on-chain/off-chain/IPFS per the TrustRouter routing decision) is exactly the scenario where divergent copies across systems become a live operational failure mode -- reconciling that divergence is core day-to-day data-engineering work, so I rate it well above CQ but still behind IQ because consistent-but-wrong data is no better than inconsistent-but-wrong data; correctness at the source has to come first. CQ (completeness, timeliness) I rank lowest of the three: an incomplete or stale record is usually a gating/scheduling problem (delay ingestion until the record is complete, or flag it as provisional) rather than a trust-corruption problem the way inaccurate values or inconsistent copies are -- it affects when and whether you write, not whether what you eventually write is truthful. This is a judgement call about relative severity of failure modes for immutable storage specifically, not a claim that completeness or timeliness are unimportant in general data quality practice. The comparison between IQ and RQ was the closer one of the two gaps, since both bear directly on data trustworthiness in a way CQ's more schedule-oriented dimensions do not.

## Sources cited

shared knowledge: trustrouter_expert_questionnaire_v5_real_survey_instrument.md, shared knowledge: trustrouter_concept_paper_primer.md, data_quality_and_polyglot_persistence.md, general_knowledge (all claims verified genuine)
