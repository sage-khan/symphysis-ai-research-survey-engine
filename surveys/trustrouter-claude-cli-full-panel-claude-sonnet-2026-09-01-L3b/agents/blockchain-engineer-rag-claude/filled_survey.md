# Filled survey: blockchain-engineer-rag-claude

- Agent ID: `blockchain-engineer-rag-claude`
- Role / expertise: Blockchain / DLT Engineer
- Model: claude_cli/sonnet
- DID: `did:key:z6MkopvxUWWWCS4idsrstN99GZf9TsfLRkdw69bu1hJ8anGq`
- RAG: enabled, corpus surveys/trustrouter-hawc-bwm/rag_corpora/blockchain-engineer
- Samples accepted: 3 (requested: 3 independent attempts)

## Summary

| Sample | Best | Worst |
|---|---|---|
| 0 | T_chain | T_history |
| 1 | T_chain | T_history |
| 2 | T_chain | T_history |

## Sample 0

**Best:** T_chain (Custody chain)  
**Worst:** T_history (Historical track record)

### Best-to-Others

| Criterion | Rating |
|---|---|
| T_source (Source credentials) | 3 |
| T_chain (Custody chain) | 1 |
| T_history (Historical track record) | 5 |

### Others-to-Worst

| Criterion | Rating |
|---|---|
| T_source (Source credentials) | 3 |
| T_chain (Custody chain) | 5 |
| T_history (Historical track record) | 1 |

### Reasoning

In a permissioned-ledger deployment for construction-project data, T_chain (custody chain integrity from creation to submission) is the criterion that most directly maps onto what blockchain/DLT technology actually verifies and enforces: hash chains, signed hand-offs, timestamped submission events, and tamper-evidence of the path data took before it hit the ledger. This is the layer where the technology's core value proposition (immutability, cryptographic linkage of custody events) is realized, so from a technical-feasibility and tamper-evidence standpoint it is the most load-bearing sub-part of Provenance Trust. T_source (who produced it -- credentials of the person/organisation) matters but is largely an off-chain, identity/PKI-management question that DLT can record but not itself establish; it's a necessary input, not something the ledger verifies dynamically. T_history (track record) is the weakest of the three for a routing decision: it's a slow-moving, reputational aggregate that is useful as a prior but doesn't tell you anything about the specific record under consideration, and a bad-history source can still submit a well-custodied, verifiable record (and vice versa) -- so it has the least direct bearing on whether this particular piece of data deserves on-chain trust. This ranking reflects my own engineering judgement about where DLT mechanisms actually add verifiable value (custody/chain-of-hashes) versus where they merely store an externally-asserted attribute (source credentials, historical reputation); the reference material (Rouhani and Deters 2021, per blockchain_trust_and_attack_resistance.md) supports treating provenance and auditing/accountability as core O'Hara data-trust properties operationalized via ledger-recorded transaction history, which aligns with weighting the chain-of-custody component highly, but it does not itself rank T_source vs T_history against each other, so that part of the ordering is my own judgement call. The comparison between T_source and T_history is somewhat close -- both are 'off-ledger' inputs -- but I lean toward source credentials being marginally more decision-relevant per-record than a historical aggregate.

## Sample 1

**Best:** T_chain (Custody chain)  
**Worst:** T_history (Historical track record)

### Best-to-Others

| Criterion | Rating |
|---|---|
| T_source (Source credentials) | 3 |
| T_chain (Custody chain) | 1 |
| T_history (Historical track record) | 6 |

### Others-to-Worst

| Criterion | Rating |
|---|---|
| T_source (Source credentials) | 3 |
| T_chain (Custody chain) | 6 |
| T_history (Historical track record) | 1 |

### Reasoning

From a blockchain/DLT engineering standpoint focused on tamper-evidence, T_chain (custody-chain integrity from creation to submission) is the criterion that maps most directly onto what a ledger can actually enforce and verify: hash-linking, timestamping, and signature-at-each-handoff give a cryptographically checkable trail of whether the record was altered en route. This is the core technical value proposition of putting construction data on-chain at all -- it converts a trust claim into a verifiable proof. T_source (who produced the data -- credentials of a person/organisation) matters as the initial trust anchor and identity check, but it is essentially a one-time, PKI/identity-style attestation that doesn't tell you anything about what happened to the data afterward -- a credentialed source's data can still be corrupted or substituted in transit if custody isn't cryptographically chained, so I rate it well below T_chain but above T_history. T_history (the source's track record) is the softest of the three: it's a statistical, reputation-based signal aggregated over past behavior, not a per-transaction verifiable property, and it is the least amenable to cryptographic enforcement -- a good track record doesn't prove this specific record's integrity, and a blockchain can't natively validate 'reliability over time' the way it can validate a hash chain. This ordering follows the same logic as the adaptive-trust framework in Rouhani and Deters (2021), where provenance/audit-trail completeness directly gates how much validation/consensus effort a piece of data needs -- custody-chain-style evidence is what that framework treats as actionable, machine-checkable trust input, whereas historical reputation is a slower-moving, softer prior. The gap between T_chain and T_history is large (6) because one is cryptographically verifiable per-record and the other is a probabilistic aggregate; T_source sits in between because it's verifiable (via PKI/identity) but static and doesn't capture in-transit integrity. This is a genuine judgement call from an engineering lens -- a compliance or legal-admissibility-focused reviewer might rank T_source higher, so I flag this comparison as less than fully clear-cut.

## Sample 2

**Best:** T_chain (Custody chain)  
**Worst:** T_history (Historical track record)

### Best-to-Others

| Criterion | Rating |
|---|---|
| T_source (Source credentials) | 2 |
| T_chain (Custody chain) | 1 |
| T_history (Historical track record) | 6 |

### Others-to-Worst

| Criterion | Rating |
|---|---|
| T_source (Source credentials) | 3 |
| T_chain (Custody chain) | 6 |
| T_history (Historical track record) | 1 |

### Reasoning

As a DLT engineer thinking about what a chain/routing decision actually needs to verify for a given construction record, I ranked T_chain (custody chain) as Best. Custody-chain integrity -- what happened to the record between creation and submission -- is precisely the property that blockchain/DLT tooling is technically built to enforce and make tamper-evident: hash-linking, per-hop signatures, and timestamping give a verifiable, per-record audit trail, which is the core engineering value-add DLT brings over conventional storage. This lines up with the O'Hara-property framing summarized in [blockchain_trust_and_attack_resistance.md] (Rouhani and Deters 2021), where 'auditing' and per-asset endorsement (trust computed per data asset, not just per owner) map most directly onto custody-chain integrity, and where the adaptive-validation mechanism keys off exactly this kind of per-transaction trust signal rather than a static reputation score. T_source (who authored it, i.e. their credentials) is a real and necessary prior -- a perfectly preserved custody chain around data from an unqualified source is still weak data -- so I placed it in the middle, meaningfully more important than T_history but clearly behind T_chain for a per-record routing decision. T_history (has this source been reliable historically) I rated Worst: it is a lagging, aggregate signal about the source in general, not about the specific record being routed. A historically reliable source can still submit a tampered or erroneous record, and a new/unproven source can still submit a perfectly custody-verified one; from an engineering feasibility and tamper-evidence standpoint, track record is useful as a coarse prior risk-weighting but carries the least direct bearing on whether *this* record deserves on-chain trust. This is a judgement call about relative weighting rather than something directly stated in the reference material, though it is consistent with the emphasis in [blockchain_trust_and_attack_resistance.md] on per-transaction/per-asset trust computation over static owner reputation alone. The Best/Source comparison (2x) was the closest call in this set -- source credentials are not far behind custody chain in importance, and a case could reasonably be made either way there.
