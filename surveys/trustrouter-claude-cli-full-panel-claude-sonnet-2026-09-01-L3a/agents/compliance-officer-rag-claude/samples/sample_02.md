# Sample 3 of 3

- Best: IQ
- Worst: RQ

## Stated reasoning (submitted with the answer)

From a compliance-officer standpoint, IQ (accuracy, validity, uniqueness) is the most fundamental cluster: if the underlying values in a construction record are wrong, invalid, or duplicated, no amount of completeness, timeliness, or cross-source consistency can rescue the record's evidentiary or regulatory value. This mirrors GDPR Article 5(1)(d)'s accuracy principle and the general audit logic that a record's core factual correctness is a precondition for everything downstream -- once written to an immutable ledger, an inaccurate value becomes a permanent compliance liability (per gdpr_and_data_governance.md's discussion of the erasure/immutability tension, where the underlying quality of what gets committed matters precisely because it cannot later be corrected). CQ (completeness + timeliness) matters for meeting disclosure and reporting obligations (e.g. energy performance or building-code disclosure windows) but a complete, on-time record built on inaccurate values is still non-compliant, so I rank it below IQ. RQ, defined here narrowly as consistency across sources, is the least critical of the three for most construction records: many records originate from a single authoritative source (a single sensor, a single certifying engineer) where cross-source consistency is not even applicable, and where it is applicable it functions more as a secondary fraud/discrepancy check than as a primary quality determinant. The gap between IQ and RQ is real but not extreme -- consistency checks remain a legitimate red flag in disputes -- so I placed it at 6 rather than 9, reflecting a considered but not maximal separation. This is a judgement call grounded in the shared knowledge instrument's definitions (IQ = accuracy/validity/uniqueness, CQ = completeness/timeliness, RQ = consistency across sources) plus general regulatory-compliance reasoning about which failures are correctable versus terminal once data is committed on-chain; it is not drawn from a specific empirical ranking in the cited sources.

## Sources cited

shared knowledge: trustrouter_expert_questionnaire_v5_real_survey_instrument.md, shared knowledge: trustrouter_concept_paper_primer.md, gdpr_and_data_governance.md, general_knowledge (all claims verified genuine)
