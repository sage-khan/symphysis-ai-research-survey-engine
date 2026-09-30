# Filled survey: structural-engineer-base-claude

- Agent ID: `structural-engineer-base-claude`
- Role / expertise: Structural Engineer
- Model: claude_cli/haiku
- DID: `did:key:z6MkwHPjNHbEfDhha3TFbbzwGmk6cFQ7di85Qq6pNXn25w2M`
- RAG: disabled
- Samples accepted: 3 (requested: 3 independent attempts)

## Summary

| Sample | Best | Worst |
|---|---|---|
| 0 | C | IC |
| 1 | PT | L |
| 2 | Q | IC |

## Sample 0

**Best:** C (Criticality)  
**Worst:** IC (Independent Confirmation)

### Best-to-Others

| Criterion | Rating |
|---|---|
| Q (Quality) | 2 |
| PT (Provenance Trust) | 2 |
| V (Verification Strength) | 3 |
| IC (Independent Confirmation) | 4 |
| L (Legal Compliance) | 3 |
| C (Criticality) | 1 |

### Others-to-Worst

| Criterion | Rating |
|---|---|
| Q (Quality) | 3 |
| PT (Provenance Trust) | 3 |
| V (Verification Strength) | 2 |
| IC (Independent Confirmation) | 1 |
| L (Legal Compliance) | 2 |
| C (Criticality) | 4 |

### Reasoning

As a chartered structural engineer responsible for decades-long liability dossiers serving institutional owners, insurers, and regulators, I rank Criticality as the dominant factor because the consequence of error in construction records is not merely inconvenient—it is potentially catastrophic and personally liable. Structural data for a public asset like Hospital Real bears on public safety, regulatory compliance, and insurance validity. Criticality sets the evidentiary bar: if something is low-criticality (e.g., decorative finishes), the same standard of provenance, quality, and verification is less essential; if high-criticality (e.g., primary structural capacity), all other factors must be excellent. No amount of independent confirmation, legal compliance, or verification strength can compensate for trivial data, nor can they solve data that is fundamentally flawed or untrustworthy at its source. Quality and Provenance Trust are close seconds—I rank them equally at 2x versus Criticality because data from a chartered engineer (PT) and technically sound data (Q) are professional necessities. But criticality slightly dominates because excellent provenance for unimportant data is less valuable than weak provenance for critical data (though unacceptable). Verification Strength and Legal Compliance (both 3x) matter for audit trails and regulatory longevity, but they are secondary to having critical, high-quality data from trusted sources. Independent Confirmation ranks worst because while reassuring, it does not substitute for foundational trust in the original source or technical quality. One authoritative, qualified source meeting regulatory requirements is sufficient if it is reliable; multiple unqualified or weakly sourced confirmations do not fix the underlying problem. Reference: shared knowledge: trustrouter_expert_questionnaire_v5_real_survey_instrument.md (definitions of Q, PT, V, IC, L, C and reference scenario context).

## Sample 1

**Best:** PT (Provenance Trust)  
**Worst:** L (Legal Compliance)

### Best-to-Others

| Criterion | Rating |
|---|---|
| Q (Quality) | 2 |
| PT (Provenance Trust) | 1 |
| V (Verification Strength) | 3 |
| IC (Independent Confirmation) | 4 |
| L (Legal Compliance) | 5 |
| C (Criticality) | 3 |

### Others-to-Worst

| Criterion | Rating |
|---|---|
| Q (Quality) | 3 |
| PT (Provenance Trust) | 5 |
| V (Verification Strength) | 2 |
| IC (Independent Confirmation) | 1 |
| L (Legal Compliance) | 1 |
| C (Criticality) | 2 |

### Reasoning

As a structural engineer responsible for capacity dossiers relied upon by institutional owners, insurers, and regulatory authorities over decades, I rank Provenance Trust as the most important trust dimension and Legal Compliance as the least. Here is the logic: In a multi-stakeholder, multi-decade scenario where structural data is handed off repeatedly and relied upon by parties who cannot directly re-verify the underlying calculations or site conditions, knowing that data originated from a qualified, chartered structural engineer and that its custody chain is documented is foundational. Quality can be independently verified through testing or review; compliance can be checked against standards; but once provenance is compromised or unclear, it cannot be easily recovered. Data from an unknown or questionable source is unreliable regardless of technical appearance. Legal Compliance, while important, is more of a derived requirement—competent structural engineers following accepted practice typically satisfy regulatory requirements. I rate Provenance 2× more important than Quality because quality can be verified but provenance must be established upfront; 3× more important than Verification Strength because cryptographic signatures are mechanisms, not substitutes for source trust; and 4× more important than Independent Confirmation because structural design, in practice, often rests on a single qualified designer with independent review, not multiple parallel confirmations. Quality and Criticality are rated 2–3× more important than Compliance because the core trust assessment is about the data itself and its source, while compliance is a constraint that follows from those.

## Sample 2

**Best:** Q (Quality)  
**Worst:** IC (Independent Confirmation)

### Best-to-Others

| Criterion | Rating |
|---|---|
| Q (Quality) | 1 |
| PT (Provenance Trust) | 2 |
| V (Verification Strength) | 2 |
| IC (Independent Confirmation) | 4 |
| L (Legal Compliance) | 2 |
| C (Criticality) | 2 |

### Others-to-Worst

| Criterion | Rating |
|---|---|
| Q (Quality) | 4 |
| PT (Provenance Trust) | 2 |
| V (Verification Strength) | 2 |
| IC (Independent Confirmation) | 1 |
| L (Legal Compliance) | 2 |
| C (Criticality) | 2 |

### Reasoning

Quality is BEST because a structural-capacity dossier must be technically sound first. Without accurate dimensional, material property, and engineering data, no verification mechanism, legal framework, or external confirmation can remedy fundamental errors. For a structural engineer managing records serving insurers, regulators, and building owners over decades, technical fidelity of the record is foundational—if the data is wrong, the building itself is at risk regardless of provenance pedigree or cryptographic proof. Every other trust factor ultimately depends on the underlying data being correct.

Independent Confirmation is WORST because it is the most contingent and least foundational. While verification by multiple parties increases confidence, it requires availability of qualified independent assessors, which is often impractical in construction contexts. Critically, if Quality is high, Provenance Trust is established, and Verification Strength is robust (cryptographic/audit-trail evidence), independent confirmation becomes a nice-to-have rather than essential. A structural engineer can responsibly rely on a single trusted source (e.g., a chartered engineer's signed report per the reference material's provenance example) if that source is credible and verified—but cannot operate safely on data of poor quality regardless of confirmation.

The intermediate factors (Provenance Trust, Verification Strength, Legal Compliance, Criticality) are all roughly 2–4× less critical than Quality but more critical than Independent Confirmation. Provenance Trust ranks near Verification and Criticality because knowing the data originated from qualified professionals is essential to credibility, but it is secondary to the fact of technical accuracy. Legal Compliance is similarly important but somewhat derivative—compliance status flows from having correct, verified, and trustworthy data. Criticality (stakes if wrong) reflects consequence rather than trustworthiness itself; it motivates why the other factors matter, but is not a trust criterion in isolation.
