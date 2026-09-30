# Sample 3 of 3

- Best: IQ
- Worst: CQ

## Stated reasoning (submitted with the answer)

For a construction-project record being considered for blockchain storage, Intrinsic Quality (accuracy, validity, uniqueness) is the foundation: if the underlying values are wrong, duplicated, or fail validation rules, no amount of completeness, timeliness, or cross-source consistency can compensate, and writing such a record to an immutable ledger only ossifies the error at high cost to correct later. This is a core data-engineering principle applied here as domain judgement, not drawn from the reference material specifically. Representational Quality (consistency across sources) sits in the middle: in a polyglot-persistence routing context it matters a great deal, because disagreement between copies is exactly the kind of provenance ambiguity that makes a record unfit to commit as a canonical on-chain record -- but consistency presumes there is already accurate data to be consistent about, so I place it below IQ. Contextual Quality (completeness, timeliness) I rate as least critical of the three: a record that is scoped narrowly or slightly stale is still usable and can often be supplemented or reconciled with a later update, whereas an inaccurate or internally inconsistent record actively misleads downstream consumers of the ledger. This is a genuinely close call between CQ and RQ -- both are legitimate contenders for 'least important' -- but I lean toward CQ as worst because timeliness/completeness gaps are more routinely tolerated and corrected in construction data workflows (e.g., progressive completion of as-built records) than unresolved inter-source disagreement, which more directly threatens the trust guarantee blockchain storage is meant to provide. The cluster definitions (accuracy/validity/uniqueness for IQ; completeness/timeliness for CQ; consistency across copies for RQ) are taken directly from the survey instrument's glossary.

## Sources cited

shared knowledge: trustrouter_expert_questionnaire_v5_real_survey_instrument.md, general_knowledge (all claims verified genuine)
