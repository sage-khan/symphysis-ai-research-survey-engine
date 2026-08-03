# TrustRouter concept paper primer

This is a plain-English summary of the TrustRouter/BSI concept paper's actual
mathematical structure, drawn directly from the project's authoritative
schema module (`trustrouter.py`) and its published worked example
(`TRUSTROUTER_EQUATION.md`). Read this before answering any BWM comparison
below: several agents in earlier runs of this survey treated the six
dimensions inside DVS as "the whole TrustRouter calculation," which is
incomplete. There are more moving parts than that, and this primer explains
where each one fits.

## Two stages: gates, then scoring

TrustRouter is a two-stage decision framework, not one formula applied
uniformly to every data item:

1. **Constraint gates (Stage 1).** Three absolute, pre-scoring eligibility
   checks: legal and privacy compliance (e.g. GDPR), confidentiality, and
   technical feasibility (e.g. does this artefact fit the target chain's
   size and throughput limits). A gate failure is a hard block: no matter
   how well the data scores on every other dimension, a GDPR-protected or
   oversized item is routed away from immutable storage before any trust
   calculation begins. Gates are deterministic yes/no checks, not weighted
   criteria, so they are not part of this BWM elicitation: you are never
   asked to weigh a gate against another gate, or against a scored
   dimension. This distinction between constraint gates and weighted
   scoring is itself the paper's central contribution over prior blockchain
   suitability tools, which average compliance into the score instead of
   gating on it first.
2. **Multi-dimensional trust scoring (Stage 2).** Only data that passes
   every gate proceeds here. This is what the levels below elicit weights
   for.

## The composite formula (the "main formula")

```
TrustRouter = DVS x F x (1 + E) x A
```

Four top-level factors, combined **multiplicatively**, not as a weighted
sum:

- **DVS (Data Value Score)**: composite trustworthiness of the data itself.
  This is the one factor that is *further* broken down (see below); it is
  not a single number an expert rates directly.
- **F (Technical Feasibility Fit)**: how well the artefact fits ledger
  constraints (size, update rate, latency). `F = 1 - P`, where P is a
  performance penalty.
- **E (Economic Value)**: financial or asset value at stake if the data is
  corrupted or lost.
- **A (Attack Resistance)**: difficulty of undetected manipulation.

Because these four combine multiplicatively rather than as parts of one
linear sum, the L1 BWM comparison below (DVS vs. F vs. E vs. A) is eliciting
*relative importance among multiplicatively-combined factors*, a
conceptually different kind of "importance" than every other level in this
survey, where a criterion's weight is literally its share of a weighted
sum. Do not treat the L1 comparison as interchangeable with the others; it
answers "how much does getting this factor right matter to the overall
decision," not "what fraction of one total does this factor contribute."

The resulting score routes the data item to a storage tier:
`BLOCKCHAIN` at TrustRouter >= 0.80, `IPFS_HASH` between 0.60 and 0.80, and
`OFFCHAIN` below 0.60.

## DVS breaks down into six trust dimensions (the "gates, then a main
## formula, then each variable has its own formula" part)

`DVS = w_Q*Q + w_PT*PT + w_V*V + w_IC*IC + w_L*L + w_C*C`

Six lenses, this time genuinely combined as a weighted sum (this is the
level most previous survey runs stopped at):

- **Q (Quality)**: is the data technically clean?
- **PT (Provenance Trust)**: can we trust who produced it?
- **V (Verification Strength)**: cryptographic or audit-trail evidence?
- **IC (Independent Confirmation)**: do multiple independent parties agree?
- **L (Legal Compliance)**: is this data required or regulated? (Distinct
  from the Stage-1 legal *gate*: a data item can pass the legal gate and
  still score anywhere on this dimension, e.g. "regulation requires this
  data to exist" is a different question from "regulation requires
  auditability of this specific record.")
- **C (Criticality)**: how big is the impact if it is wrong?

Two of these six are themselves broken down further, one level deeper
still:

`Q = w_IQ*IQ + w_CQ*CQ + w_RQ*RQ` (ISO 25012's three quality clusters:
Intrinsic Quality [accuracy, validity, uniqueness], Contextual Quality
[completeness, timeliness], Representational Quality [consistency across
sources])

`PT = w_source*T_source + w_chain*T_chain + w_history*T_history` (source
credentials, custody chain, historical track record)

`V = w_crypto*V_crypto + w_audit*V_audit + w_diversity*V_diversity`
(cryptographic evidence such as signatures/hashes/PKI, audit-trail
completeness, diversity of independent verification sources)

## A and E also break down further

These two live at the *top* level (L1), not inside DVS, but they are each
elaborated by their own three-way BWM comparison too, exactly the same
pattern as Q/PT/V above:

`A = w_sybil*A_sybil + w_oracle*A_oracle + w_insider*A_insider`
(**attack surface**, broken into: Sybil resistance against fake-identity
attacks, Oracle resistance against sensor/device tampering, and Insider
resistance against malicious legitimate access.)

`E = w_market*E_market + w_liquidity*E_liquidity + w_demand*E_demand`
(current marketplace demand from existing buyers right now,
**tokenisation** ease, i.e. how easy this data would be to package as a
tradeable token, and future demand from regulated/AI/digital-twin growth.)

## Full picture: seven separate BWM comparisons

| Level | What it weighs | Elaborates |
|---|---|---|
| L1 | DVS, F, E, A | (root; combines multiplicatively) |
| L2 | Q, PT, V, IC, L, C | L1's DVS |
| L3a | IQ, CQ, RQ | L2's Q |
| L3b | T_source, T_chain, T_history | L2's PT |
| L3c | V_crypto, V_audit, V_diversity | L2's V |
| L3d | A_sybil, A_oracle, A_insider | L1's A |
| L3e | E_market, E_liquidity, E_demand | L1's E |

You will be asked to complete all seven in this one response. Treat each as
an independent BWM comparison: which criterion in *this specific list* is
most important, which is least, and how does every other criterion in that
same list compare to those two, on the usual 1-9 Saaty scale.

## Source

`trustrouter.py` (BSI/TrustRouter survey-app source), the project's own
declared single source of truth for this schema, and
`TRUSTROUTER_EQUATION.md` (worked numeric example from a prior elicitation
round), both in
`docs/research/Work-in-progress/potential-papers/00-trustrouter/survey-app/`
in the project-veritas repository. The constraint-gate description is from
the TrustRouter construction research paper
(`trustrouter_construction_researchpaper.tex`, same directory tree).
