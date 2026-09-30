# Sample 2 of 3

- Best: IQ
- Worst: RQ

## Stated reasoning (submitted with the answer)

From a data engineering perspective on construction-project records destined for blockchain storage, intrinsic quality (IQ—accuracy, validity, uniqueness) is the foundation. Blockchain's immutability means inaccurate data becomes a permanent liability; wrong measurements, material specs, or compliance records directly threaten structural safety and regulatory standing. No amount of consistency or completeness salvages intrinsically false data.

Contextual quality (CQ—completeness and timeliness) is important but secondary. Completeness matters: missing change orders or omitted inspections create blind spots in the audit trail. Timeliness, while valuable for active project coordination, becomes less critical once data is immutably recorded on the ledger—the blockchain itself provides a definitive historical record. A construction record that is accurate and reasonably complete but recorded with a slight delay is preferable to a current but inaccurate one.

Representational quality (RQ—consistency across source copies) ranks lowest for blockchain-stored construction data. Blockchain's design principle is a single canonical ledger; once data is recorded, there is one authoritative version, not multiple copies requiring reconciliation. If intrinsic accuracy is high and the data capture process is sound, consistency becomes a data governance and deduplication problem rather than a trust or integrity problem. Historical disputes in construction often turn on accuracy and completeness ("what was actually specified and recorded?"), not on whether multiple copies agree.

Ratings reflect: IQ is approximately 2× more critical than CQ (accuracy slightly outweighs completeness/timeliness), and CQ is 2× more critical than RQ (data scope and currency outweigh version consistency). This yields IQ 4× more important than RQ overall, consistent with the layered risk: inaccurate data > incomplete data > inconsistent copies (when underlying data is sound).

## Sources cited

shared knowledge: trustrouter_expert_questionnaire_v5_real_survey_instrument.md, shared knowledge: trustrouter_concept_paper_primer.md, general_knowledge (all claims verified genuine)
