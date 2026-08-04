# Data quality and polyglot persistence

Real, catalogued sources relevant to L2's Quality (Q) dimension and its
L3a breakdown (ISO 25012's Intrinsic/Contextual/Representational quality
clusters), and to how heterogeneous data actually gets routed across
storage systems in practice. Drawn from
the author's TrustRouter research literature review catalogue.

## Application of Polyglot Persistence to Enhance Performance of the Energy Data Management Systems, Prasad and S B, 2014 (IEEE ICAECC, Siemens Technology)

An industrial (Siemens) case study applying polyglot persistence to Energy
Data Management Systems for smart grids and smart meters: time-series
databases for high-frequency meter data, relational databases for
transactional billing data requiring ACID guarantees, and graph databases
for network-topology traversal in energy dissemination. Directly analogous
to why a single data item's Quality score (accuracy, completeness,
consistency, i.e. exactly ISO 25012's IQ/CQ/RQ clusters) needs to be
assessed per-artefact rather than assumed uniform across a data
architecture: different data types in the same energy domain have
different quality profiles and need different storage treatment.

## Multi-Model Databases: Introducing Polyglot Persistence in the Big Data World, Kosmerl, Rabuzin, and Sestak, 2018

Compares multi-model databases (a single engine supporting multiple data
models, e.g. ArangoDB, OrientDB) against true polyglot persistence
(multiple specialized databases coordinated at the application level).
Multi-model reduces operational complexity but sacrifices per-model
specialization; polyglot is preferable at extreme scale or when
best-in-class performance per data type matters more than unified query
convenience. Relevant background for why TrustRouter's routing decision
(BLOCKCHAIN vs. IPFS_HASH vs. OFFCHAIN) is itself a polyglot-persistence
decision extended with a trust dimension on top of the usual
structural/performance criteria.

## Data trust framework using blockchain technology and adaptive transaction validation, Rouhani and Deters, 2021 (IEEE Access, DOI 10.1109/ACCESS.2021.3091327)

See the blockchain-engineer corpus for the full summary. Relevant here
specifically for its data trust properties taxonomy (discovery,
provenance, access control, auditing, accountability), which overlaps with
what Provenance Trust (PT) and Independent Confirmation (IC) are trying to
capture at the L2 level, from a data-engineering rather than a blockchain
angle: a data pipeline's own audit logging and lineage tracking is often
the first-hand source of evidence a Verification Strength (V) or
Provenance Trust (PT) score should actually be based on.
