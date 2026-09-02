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
| T_chain (Custody chain) | 3 |
| T_history (Historical track record) | 5 |

### Others-to-Worst

| Criterion | Rating |
|---|---|
| T_source (Source credentials) | 5 |
| T_chain (Custody chain) | 2 |
| T_history (Historical track record) | 1 |

### Reasoning

As a chartered structural engineer responsible for structural-capacity dossiers relied upon by insurers, regulators, and building owners over decades, I rank these criteria from the perspective of data trust for construction records, particularly those with long-term liability and safety implications. T_source (source credentials) is BEST because the identity and professional credentials of whoever produced structural data—measurements, calculations, test results—is the foundational gate for trustworthiness. In structural engineering, professional licensing (PE, CEng, or equivalent) carries legal responsibility; without credible authorship, the entire chain of reliance collapses, regardless of chain integrity or historical reputation. T_history (historical track record) is WORST because while useful context, it is backward-looking and indirect: past reliability does not guarantee this specific record's integrity or that the current submitter has not altered data. It provides corroborating evidence but not direct control. T_chain ranks between them because custody-chain integrity is significant—data should not be corrupted in transit—but can be partially mitigated through cryptographic controls and audit trails. A record from a credible, licensed source carries higher baseline confidence even if chain history is complex; conversely, a record with perfect chain integrity but unknown or uncredentialed origin is unreliable for structural decisions. This ranking reflects the professional hierarchy of evidence in structural engineering: credible authorship and professional accountability anchor trust, chain integrity preserves it, and historical reputation provides supporting context.

## Sample 1

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

As a structural engineer responsible for capacity dossiers, source credentials (T_source) are foundational: data from a qualified, licensed structural engineer or architect carries intrinsic credibility; data from an unqualified source is unreliable regardless of what happens to it afterward. A well-credentialed source establishes the baseline that construction data is competent before any further verification. Custody chain (T_chain) is also critical—data integrity can be compromised en route to blockchain, and for records serving insurers and authorities over decades, an unbroken audit trail is essential. However, source credentials come first: they determine whether the data was correct at inception. A perfectly-preserved chain cannot rescue fundamentally incorrect structural analysis from an uncredentialed source. T_chain rates 2x less critical than T_source because blockchain and custody verification can provide post-hoc assurance of data integrity, but source credentials determine what data existed before any chain exists. Historical track record (T_history) is the least influential factor. While a source with a long record of reliable output provides useful corroboration, it should not override current credentials. A newly-qualified structural engineer (no history) is trustworthy if properly licensed and competent. Conversely, an engineer with poor historical performance should not be relied upon regardless. T_source and T_chain both outweigh T_history by large margins because immediate, verifiable factors (credentials and custody) are more actionable than past performance, especially when professional licensing standards already incorporate quality expectations. T_history functions as supporting evidence rather than a primary determinant of whether to route data on-chain.

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
| T_chain (Custody chain) | 3 |
| T_history (Historical track record) | 1 |

### Reasoning

As a structural engineer responsible for dossiers that serve insurers, regulators, and building owners over decades, I rank T_source (source credentials) as best because professional authority is foundational: a dossier prepared by a chartered engineer or equivalent carries legal liability and institutional standing that no amount of chain integrity can substitute for. Conversely, data that is poorly sourced but perfectly preserved remains professionally unreliable. T_history ranks worst because while past performance is useful context for calibrating risk, it is the least directly actionable for evaluating a specific dossier—even a reliable source can fail once, and historical track record cannot substitute for verifying the credentials and integrity of the data at hand. T_chain ranks between them: custody integrity is critical (especially in blockchain context where tamper-detection is the core value proposition), but it remains secondary to establishing that the source itself is credible. A well-preserved record of garbage data is still garbage data. In the context of institutional construction records spanning decades, source credentials determine whether the data has professional authority; chain integrity verifies it has not been corrupted; history provides supporting context but cannot override either of the former.
