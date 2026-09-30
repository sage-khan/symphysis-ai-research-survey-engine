# Sample 2 of 3

- Best: IQ
- Worst: RQ

## Stated reasoning (submitted with the answer)

From a data engineering specialist's perspective on construction-project datasets destined for blockchain storage: Intrinsic Quality (IQ) is the foundational criterion because inaccuracy, invalidity, or duplication of core data creates an irreversible contamination of an immutable ledger. On a blockchain, the correctness of recorded facts—structural dimensions, contractual terms, inspection results, timestamps—cannot be retroactively repaired without breaking the chain's integrity guarantees. A construction record's accuracy and uniqueness are prerequisite to any downstream trust claim. Contextual Quality (CQ) ranks second: while completeness and timeliness are important operational concerns, an incomplete but accurate record (which can be enriched later in the pipeline) is preferable to a complete but inaccurate one; and delayed-but-correct data can still be reliably stored and audited. Representational Quality (RQ)—consistency across sources—ranks last in isolation because for a single construction-project record being committed to blockchain, internal consistency of that record is not the primary quality concern; consistency matters more in multi-source scenarios where reconciliation and deduplication are needed upstream, which is a separate data integration problem from whether the committed record itself is trustworthy. RQ also depends on IQ being met first: identical but wrong versions achieve consistency without trust. This ranking reflects the polyglot-persistence principle noted in the reference material (Prasad and S B, 2014): different data types and pipeline stages have different quality profiles; for immutable ledgers, intrinsic correctness dominates operational scheduling concerns.

## Sources cited

data_quality_and_polyglot_persistence.md, shared knowledge: trustrouter_expert_questionnaire_v5_real_survey_instrument.md, shared knowledge: trustrouter_concept_paper_primer.md, general_knowledge (all claims verified genuine)
