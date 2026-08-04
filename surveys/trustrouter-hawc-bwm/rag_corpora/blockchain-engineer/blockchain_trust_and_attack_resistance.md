# Blockchain trust, attack resistance, and the oracle problem

Real, catalogued sources relevant to the L1 Attack Resistance (A) factor and
its L3d breakdown (Sybil / Oracle / Insider resistance), and to L2's
Verification Strength (V) and Provenance Trust (PT) dimensions. Drawn from
the author's TrustRouter research literature review catalogue (never fabricated; each entry below is that catalogue's own
recorded content summary and findings for the cited source).

## Data trust framework using blockchain technology and adaptive transaction validation, Rouhani and Deters, 2021 (IEEE Access, DOI 10.1109/ACCESS.2021.3091327)

Proposes a comprehensive blockchain-based data trust framework for
trustworthy data sharing, implementing O'Hara's eight data trust
properties (discovery, provenance, access control, access, identity
management, auditing, accountability, impact) on a permissioned blockchain
(Hyperledger Fabric). Its trust model uses three parameters: data owner
endorsement/reputation, data asset endorsement, and the owner's own
confidence level in the dataset, all recorded on an immutable ledger and
updated with every transaction. Its adaptive transaction validation
dynamically adjusts how many signatures/how much consensus a transaction
needs based on the computed trust value: higher trust needs fewer
signatures, lower trust triggers full Byzantine consensus. Relevant to
Verification Strength (audit-trail completeness) and to how a trust score
can directly gate the cost/strength of the validation mechanism applied to
a piece of data, the same principle TrustRouter applies to storage-tier
routing rather than validator count.

## SoK: Bridging Trust into the Blockchain, a Systematic Review on On-Chain Identity, Vaziry et al., 2024 (arXiv:2407.17276, TU Berlin)

A systematisation-of-knowledge review (2,232 papers screened down to 13)
on establishing trusted, privacy-compliant on-chain identities for
regulatory compliance (AML/KYC/CTF), covering zero-knowledge proofs, PKI,
and web-of-trust mechanisms. Identifies two trust gaps directly relevant to
Insider and Sybil resistance: (1) trusting that an on-chain identity truly
represents the physical entity behind it (the digital-physical identity
mapping problem, i.e. how a Sybil attack is even possible in the first
place), and (2) trusting the identity *issuers* that vouch for on-chain
identities. Useful background for reasoning about A_sybil and A_insider:
the paper frames both as instances of the same underlying "who is really
behind this identity" question.

## A Survey of Trust Management for Internet of Things, Konsta, Lluch Lafuente, and Dragoni, 2023 (IEEE Access, vol. 11, pp. 122175-122204, DOI 10.1109/ACCESS.2023.3327335)

Systematic survey of 100+ IoT trust-management papers, categorised across
nine dimensions (information gathering, trust update, trust formation,
propagation, threat model, and others) and by underlying technology
(machine learning, blockchain, fuzzy logic, game theory). Directly relevant
to A_oracle (sensor/device tampering resistance): IoT trust research treats
sensor/device nodes as the thing being trusted, exactly the oracle problem
TrustRouter's A_oracle criterion targets when the "device" in question is
whatever sensor or gateway is attesting to the external fact a smart
contract or trust score depends on. The survey's identified gap, that most
IoT trust research asks "is this device reliable" rather than "where should
this device's data be stored/routed," is precisely the gap TrustRouter's
routing decision (as opposed to node reputation alone) addresses.

## Astraea: Decentralized Blockchain Oracle, Adler, Berryhill, Veneris, et al., 2018 (IEEE Cybermatics)

Proposes Astraea, a voting-game-based decentralized oracle for bringing
external facts onto a blockchain: "voters" make low-risk/low-reward random
propositions resistant to manipulation, while "certifiers" stake
high-risk/high-reward bets on outcomes. Directly relevant to A_oracle: the
oracle problem is that smart contracts can only act on data already on the
blockchain, so they need a trusted mechanism to attest to real-world facts
(sensor readings, off-chain events) before that data can be used on-chain,
exactly the attack surface A_oracle scores.
