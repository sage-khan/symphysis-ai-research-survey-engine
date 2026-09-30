# Sample 2 of 3

- Best: V_crypto
- Worst: V_diversity

## Stated reasoning (submitted with the answer)

From an engineering standpoint, cryptographic evidence (signatures, hashes, PKI) is the load-bearing mechanism that makes any ledger-based system tamper-evident at all: without a signed hash chain, there is no cryptographic proof that a construction record was not altered post-hoc, and the other two sub-parts become unverifiable claims layered on an untrusted substrate. This makes V_crypto the clear Best. Audit trail completeness (who did what, when) is genuinely valuable for construction dispute resolution and regulatory accountability, and is one of O'Hara's eight data-trust properties operationalised on a permissioned ledger in the Rouhani and Deters (2021) framework (per blockchain_trust_and_attack_resistance.md), but on a blockchain it is largely a structural consequence of combining PKI-based identity with an append-only ledger -- once you have V_crypto and a logging discipline, a reasonably complete audit trail follows almost automatically from the architecture, so I rate it a clear second (3x behind Best) rather than near-Best. Diversity of independent verification sources is a real and separate concern (guarding against a single compromised or colluding attestor), but in the TrustRouter hierarchy this concern substantially overlaps with the Attack Resistance factor's own Sybil/Insider decomposition (A_sybil, A_insider, per the shared survey instrument's Section 3.6), meaning its marginal contribution specifically within Verification Strength is the smallest of the three -- it addresses a risk that is already partly captured elsewhere in the composite. That makes it Worst, though I note the V_audit vs V_diversity comparison is not overwhelmingly one-sided; both are plausibly mid-tier, and reasonable engineers could rank them closer together than I have.

## Sources cited

shared knowledge: trustrouter_expert_questionnaire_v5_real_survey_instrument.md, blockchain_trust_and_attack_resistance.md, general_knowledge (all claims verified genuine)
