# GDPR, data governance, and the blockchain-immutability tension

Real, catalogued sources relevant to the L1 constraint gates (legal and
privacy, confidentiality) described in the concept-paper primer, and to
L2's Legal Compliance (L) dimension. Drawn from
`docs/research/LITERATURE_REVIEW_CATALOG.csv` in the project-veritas
literature bank.

## Data Management Challenges in Blockchain-Based Applications, Wilson, Adu-Duodu, Rana, and Solaiman, 2019

Identifies core data-management challenges in blockchain applications:
scalability, privacy, access control, and query inefficiency, all arising
because blockchain's core properties (immutability, decentralization,
transparency) directly conflict with several traditional data-management
requirements, most importantly the GDPR's right to erasure, which cannot
be honoured against an immutable ledger. Its conclusion is that blockchain
is a complement to, not a replacement for, traditional databases: use
blockchain for immutability requirements (audit logs, provenance) and
decentralized trust; use a traditional database for high-throughput OLTP
workloads and complex queries. This is exactly the reasoning a Legal
Compliance (L) or a Stage-1 legal/privacy gate assessment needs to apply
per data item: does this specific artefact actually need the immutability
blockchain provides, or would putting it there create a compliance
liability with no offsetting benefit.

## SoK: Bridging Trust into the Blockchain, a Systematic Review on On-Chain Identity, Vaziry et al., 2024 (arXiv:2407.17276, TU Berlin)

See the blockchain-engineer corpus for the full summary. Relevant here for
its framing of on-chain identity as a *regulatory compliance* problem
(AML/KYC/CTF) as much as a technical one: establishing a privacy-compliant
on-chain identity is itself subject to the same GDPR tension the Stage-1
confidentiality gate is meant to catch before a data item ever reaches
DVS-level trust scoring.

## Five-Year Review of Blockchain in Construction Management: Scientometric and Thematic Analysis (2017-2023), Gartoumi, 2024 (Automation in Construction, 168:105773)

See the bim-coordinator corpus for the full summary. Relevant here for its
finding that construction-sector blockchain adoption has grown for five
years without the industry developing rigorous decision criteria for
when blockchain storage is legally and practically appropriate, the
governance gap the constraint-gate stage is designed to close before any
weighted trust score is even computed.
