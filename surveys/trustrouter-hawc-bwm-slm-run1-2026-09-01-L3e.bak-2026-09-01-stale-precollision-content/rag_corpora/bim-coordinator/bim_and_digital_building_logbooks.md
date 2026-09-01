# BIM, Digital Building Logbooks, and decentralized identity for construction data

Real, catalogued sources relevant to Provenance Trust (PT), Independent
Confirmation (IC), and Legal Compliance (L), from the construction/BIM
domain specifically. Drawn from
the author's TrustRouter research literature review catalogue.

## Leveraging IFC Semantics and W3C Decentralized Identifiers for Digital Building Logbooks in Construction and Deep Renovation, Kochovski et al., 2026 (Automation in Construction, vol. 189, article 107065, DOI: 10.1016/j.autcon.2026.107065)

Presents BUILDCHAIN DBL, a decentralized Digital Building Logbook
architecture combining an IFC-aligned ontology (semantically integrating
BIM, legacy CAD, sensor logs, and inspection records) with W3C
decentralized identifiers and verifiable credentials on an Ethereum
smart-contract layer. Empirically measured on a real Ethereum Holesky
testnet: on-chain authentication averaged 2.07ms, on-chain DID resolution
(a read) averaged 88ms, and on-chain DID creation/revocation (writes) were
roughly an order of magnitude slower than reads. Directly relevant to
Provenance Trust (T_source, T_chain): this is a real, measured example of
what "source credentials" and "custody chain" mean operationally for
construction data specifically, cryptographically verifiable identity
issuance and revocation, not just a policy statement. Co-authored by
researchers directly affiliated with this project's own TrustRouter
research (UGR and University of Ljubljana), so this is not an external
analogy but the same research programme's own published, peer-reviewed
result on the identity-and-provenance layer TrustRouter's PT dimension is
scoring.

## Information Management according to BS EN ISO 19650: Guidance Part 2, UK BIM Framework (CIC, BSI, CDBB, UK BIM Alliance), 2019

Practitioner guidance on BIM information management processes for project
delivery under ISO 19650, covering BIM execution plans, delivery-team
competency/capacity assessment, and federation strategy. Relevant
background for Independent Confirmation (IC, do multiple independent
parties agree) in a BIM context: ISO 19650's information-delivery process
already requires multiple parties (lead appointed party, task teams) to
independently validate federated models before they are accepted, which is
the real-world mechanism an IC score for BIM data would actually be
assessing.

## Five-Year Review of Blockchain in Construction Management: Scientometric and Thematic Analysis (2017-2023), Gartoumi, 2024 (Automation in Construction, 168:105773)

Scientometric and thematic analysis of 237 documents on blockchain in
construction management, identifying eight thematic application
categories and noting that despite five years of growing publication
volume, the construction industry still lacks rigorous, calibrated
decision criteria for when blockchain-backed storage is actually
warranted for a given construction data item, precisely the gap this
survey's TrustRouter weight elicitation exists to close.
