# Filled survey: bim-coordinator-rag-claude

- Agent ID: `bim-coordinator-rag-claude`
- Role / expertise: BIM Coordinator
- Model: claude_cli/haiku
- DID: `did:key:z6MkgKPXYGDwJ56epiD68PaM63oukrBdhu5ziYGo84AZKm9n`
- RAG: enabled, corpus surveys/trustrouter-hawc-bwm/rag_corpora/bim-coordinator
- Samples accepted: 3 (requested: 3 independent attempts)

## Summary

| Sample | Best | Worst |
|---|---|---|
| 0 | T_source | T_history |
| 1 | T_chain | T_history |
| 2 | T_source | T_history |

## Sample 0

**Best:** T_source (Source credentials)  
**Worst:** T_history (Historical track record)

### Best-to-Others

| Criterion | Rating |
|---|---|
| T_source (Source credentials) | 1 |
| T_chain (Custody chain) | 4 |
| T_history (Historical track record) | 6 |

### Others-to-Worst

| Criterion | Rating |
|---|---|
| T_source (Source credentials) | 6 |
| T_chain (Custody chain) | 5 |
| T_history (Historical track record) | 1 |

### Reasoning

T_source (source credentials) is the foundational criterion for construction data destined for long-term institutional or blockchain storage. In multi-stakeholder BIM environments like the Hospital Real scenario, ISO 19650's information-delivery process mandates party identification and independent validation by named, qualified parties. Without knowing who produced data and their professional credentials (structural engineer, certified surveyor, approved inspection bureau), the other trust factors become conditional or purely confirmatory. In federated models spanning decades with multiple stakeholders (owners, insurers, authorities), accountability to an identified, credentialed source is non-negotiable and legally mandatory. T_chain (custody integrity) ranks second: data quality degrades measurably through schema conversions, coordinate-system transforms, and model federation steps. Knowing the chain matters critically to detect whether intermediate modifications compromised the data. However, chain integrity is only actionable if the originating source is trustworthy; perfect chain evidence from an unqualified source provides false confidence. T_history (prior track record) ranks worst because it is supplementary rather than foundational: historical reliability provides context but cannot be applied to new data sources, new delivery parties, or novel data types—all common in renovation projects. While past performance matters for institutional decision-making, it is not mandatory (new parties lack it), not directly observable in the data itself, and does not guarantee current performance if circumstances have changed. The rating gap between source and chain (4:1) reflects that chain is significant but conditional on source. The gap between source and history (6:1) reflects that source is mandatory and observable, while history is optional and retrospective. The gap between chain and history (5:1) reflects that chain directly affects current trustworthiness, while history is supportive context. This ranking aligns with professional practice in multi-party BIM delivery: party identification and responsibility matrices are established first (source); chain-of-custody procedures (who modified what, when) are then implemented; and source reputation is accumulated over time (history).

## Sample 1

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
| T_source (Source credentials) | 2 |
| T_chain (Custody chain) | 5 |
| T_history (Historical track record) | 1 |

### Reasoning

For construction-project records routed to blockchain storage in a multi-stakeholder BIM environment, custody chain integrity is the most critical of the three PT sub-parts. In federated BIM models under ISO 19650, independent validation and acceptance depend on verifiable integrity from source to submission—precisely the tamper-evidence problem blockchain is designed to solve. Data with excellent source credentials and a reliable originator is worthless if it has been corrupted, altered undetectably, or improperly handed off in intermediate steps. In my role coordinating multi-party federated models, I have observed that the weakest link in data integrity is typically the custody and handoff process, not the initial creation. The reference material notes that 'decentralised ledgers improve tamper-evidence (changes become detectable),' which directly addresses the custody-chain risk. Historical track record, while valuable for ongoing trust relationships and stakeholder confidence, is the least actionable for a single submission decision. A newly formed team or organization could submit trustworthy data if source credentials are verifiable and custody is maintained; conversely, a historically reliable source's data becomes unsafe if the chain of custody is broken. T_source falls between the two: knowing who created the data matters, but only if that creation is followed by a protected custody chain to the point of blockchain submission.

## Sample 2

**Best:** T_source (Source credentials)  
**Worst:** T_history (Historical track record)

### Best-to-Others

| Criterion | Rating |
|---|---|
| T_source (Source credentials) | 1 |
| T_chain (Custody chain) | 4 |
| T_history (Historical track record) | 6 |

### Others-to-Worst

| Criterion | Rating |
|---|---|
| T_source (Source credentials) | 6 |
| T_chain (Custody chain) | 4 |
| T_history (Historical track record) | 1 |

### Reasoning

As a BIM Coordinator managing federated models across multi-stakeholder renovation and new-build projects, source credentials (T_source) is foundational to all downstream trust decisions. In model federation, every federated element must be traceable to a discipline team with the authority and competence to produce that data type—structural engineers for load-bearing elements, MEP specialists for systems, surveyors for as-built dimensions. Without knowing who created the data and whether they held the relevant authority for that data class, neither custody-chain integrity nor historical track record provides actionable assurance. T_source is logically prior. T_chain (custody integrity) ranks second because, even with credible authoring, data can be corrupted in transit across authoring tools, model servers, and federation platforms—a risk I encounter regularly in multi-stage handoffs. However, custody-chain failures can only matter if the source was credible to begin with. T_history (track record) ranks last. While institutional knowledge of a consultant's or contractor's historical performance is contextually valuable, it is a heuristic supplement to direct source evaluation, not a primary trust gate. On a specific project record, what matters is whether that source holds the current authority and whether its data for this project has been protected in custody, not whether they performed well on a prior engagement. Track record can shift with personnel changes, organizational restructuring, or disciplinary transitions. For construction-project data destined for blockchain storage or digital building logbooks serving multi-decade institutional and regulatory use (as per the reference scenario), establishing source credentials first is the rational routing priority.
