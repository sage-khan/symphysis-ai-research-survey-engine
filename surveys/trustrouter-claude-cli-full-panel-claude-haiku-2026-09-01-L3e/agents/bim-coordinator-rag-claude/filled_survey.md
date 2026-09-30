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
| 0 | E_demand | E_liquidity |
| 1 | E_demand | E_liquidity |
| 2 | E_demand | E_liquidity |

## Sample 0

**Best:** E_demand (Future demand)  
**Worst:** E_liquidity (Tokenisation ease)

### Best-to-Others

| Criterion | Rating |
|---|---|
| E_market (Current marketplace demand) | 3 |
| E_liquidity (Tokenisation ease) | 6 |
| E_demand (Future demand) | 1 |

### Others-to-Worst

| Criterion | Rating |
|---|---|
| E_market (Current marketplace demand) | 2 |
| E_liquidity (Tokenisation ease) | 1 |
| E_demand (Future demand) | 6 |

### Reasoning

As a BIM coordinator managing long-term multi-stakeholder documentation on renovation projects, I rank future demand (E_demand) as most critical and tokenisation ease (E_liquidity) as least critical for construction project records. E_demand receives the highest importance because regulatory and technical drivers will shape adoption: ISO 19650 digital transformation, EU digital acts integration, GDPR lifecycle compliance, digital-twin standardisation, and AI-ready data structures are all institutional forces with binding regulatory weight. For public assets like Hospital Real (per the reference scenario), these future compliance and interoperability demands directly govern system decisions over a 10–30 year operational lifespan. Current marketplace demand (E_market) is intermediate—some early adoption exists in digital building logbook initiatives (Kochovski et al. 2026) and blockchain research in construction (Gartoumi 2024 notes 237 publications over five years), but uptake remains fragmented and niche. E_liquidity ranks lowest because tokenisation of construction project records is not a material use case in practice. The Gartoumi 2024 review emphasises that despite growing research volume, the construction industry still lacks calibrated decision criteria for blockchain deployment—and tokenisation is notably absent from those criteria. Construction data's value is functional (clash detection, asset tracking, renovation planning, regulatory proof) rather than financial; records are not traded as commodities. The reference material does not suggest tokenisation is relevant to the Hospital Real scenario. Ratings reflect a 3:1 importance gap between future and present demand, and a 6:1 gap between future demand and tokenisation mechanics. E_market is rated 2x more important than E_liquidity because even niche current demand outweighs speculative tradability for infrastructure decisions.

## Sample 1

**Best:** E_demand (Future demand)  
**Worst:** E_liquidity (Tokenisation ease)

### Best-to-Others

| Criterion | Rating |
|---|---|
| E_market (Current marketplace demand) | 4 |
| E_liquidity (Tokenisation ease) | 8 |
| E_demand (Future demand) | 1 |

### Others-to-Worst

| Criterion | Rating |
|---|---|
| E_market (Current marketplace demand) | 2 |
| E_liquidity (Tokenisation ease) | 1 |
| E_demand (Future demand) | 8 |

### Reasoning

From a BIM coordinator's perspective managing multi-stakeholder renovation and new-build projects over 10+ years, future regulatory demand (E_demand) is decisively more important than current marketplace adoption or tokenisation capability for construction records on blockchain.

E_demand is Best because: (1) Gartoumi 2024 documents that construction lacks calibrated criteria for blockchain adoption—the market currently exists in principle, not practice. (2) Kochovski et al. 2026 demonstrates working digital building logbooks (DBL) combining IFC semantics with W3C decentralized identifiers, which are entering regulatory frameworks, not established markets. (3) Real lifecycle pressure comes from ISO 19650's requirement that federated models be independently validated before acceptance; this is a decades-long institutional need (Hospital Real reference scenario), not a current buyer base. (4) Future demand will be driven by GDPR/EU digital acts compliance, digital-twin integration for asset management, and regulatory mandates on deep-renovation documentation—none of which depend on today's market.

E_liquidity is Worst because tokenisation of construction records is inapplicable: (1) Project records are not fungible or divisible assets—you do not trade fractional ownership of inspection certificates or RFI logs. (2) Records are owned by institutions (public bodies, facilities managers, regulators) for compliance and asset stewardship, not for secondary-market speculation. (3) GDPR and data-protection rules actively prevent the secondary-market tokenisation this criterion implies. (4) No construction professional I have worked with has ever requested the ability to tokenise or trade project documentation. The criterion, while syntactically valid, measures a non-existent use case.

E_market ranks between them: there is some immediate institutional demand (authorities, insurers) for trustworthy long-term documentation, as ISO 19650 practice demonstrates. However, this demand exists in federated BIM and ISO 19650 processes already; blockchain adds marginal value only if future regulation makes it mandatory. Current buyers are few and their demand is not blockchain-specific. Future regulatory drivers (E_demand) are far more consequential for a technology platform decision than existing (but blockchain-agnostic) institutional record-keeping.

Rating rationale: E_demand at 8× E_liquidity reflects that liquidity is essentially orthogonal to construction records. E_demand at 4× E_market reflects that future regulatory/digital-twin drivers outweigh weak current adoption. E_market at 2× E_liquidity reflects minimal but non-zero institutional demand for record-keeping, versus zero demand for tokenisation.

## Sample 2

**Best:** E_demand (Future demand)  
**Worst:** E_liquidity (Tokenisation ease)

### Best-to-Others

| Criterion | Rating |
|---|---|
| E_market (Current marketplace demand) | 4 |
| E_liquidity (Tokenisation ease) | 7 |
| E_demand (Future demand) | 1 |

### Others-to-Worst

| Criterion | Rating |
|---|---|
| E_market (Current marketplace demand) | 2 |
| E_liquidity (Tokenisation ease) | 1 |
| E_demand (Future demand) | 7 |

### Reasoning

E_demand (projected future demand) emerges as the strongest economic driver for blockchain-backed BIM data storage. Regulatory momentum is real: EU digital building passports and renovation directives mandate long-term, verifiable building records. For the Hospital Real scenario referenced—a multi-decade public asset requiring institutional ownership, insurance, and regulatory documentation—future demand is driven by lifecycle durability, compliance automation, and emerging digital-twin analytics. Kochovski et al. 2026 explicitly grounds digital building logbooks in this forward-looking regulatory and technical context.

E_market (current marketplace demand) ranks second. From 10+ years in BIM coordination, adoption of blockchain for BIM data remains limited to pilots and early research (consistent with Gartoumi 2024's observation that the industry still lacks 'rigorous, calibrated decision criteria for when blockchain-backed storage' is appropriate). Mainstream practice uses centralized BIM collaboration servers. However, current market signals do exist—research projects, institutional pilots—so this criterion is meaningfully stronger than pure speculation but significantly weaker than regulatory tailwinds.

E_liquidity (tokenisation ease) is weakest. BIM data faces structural barriers to tokenisation: fragmented multi-stakeholder ownership, highly contextual value tied to project federation and federated-model validation (ISO 19650), privacy constraints under GDPR, and liability questions. Unlike fungible commodities, building data's value is relational and context-dependent, making unit-level tradability neither technically mature nor economically sensible. From practitioner experience, I observe no emerging market for tokenised BIM data slices, and the conceptual barriers run deep.

The ratings reflect this hierarchy: E_demand is 7× more important than E_liquidity (regulatory + lifecycle + AI integration vs. structural tokenisation barriers); 4× more important than E_market (forward regulatory pressure vs. current limited adoption); E_market is 2× more important than E_liquidity (real pilots exist, but tokenisation barriers are deeper).
