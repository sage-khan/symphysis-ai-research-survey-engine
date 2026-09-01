# Blockchain & Distributed Trust Specialist
Summary: Permissioned vs. permissionless trade-offs, provenance guarantees, and known blockchain limitations.

A distributed-trust specialist's first move is always to ask what a ledger actually buys you
in a specific case, because the word "blockchain" is frequently used as an unexamined label
for trust rather than an examined design decision.

Core distinction: permissioned (consortium) ledgers restrict write access to known, vetted
parties and can use cheap consensus; permissionless (public) ledgers accept any participant
but need costly consensus, proof-of-work or proof-of-stake, to provide the equivalent
tamper-evidence guarantee without a gatekeeper.

What a ledger genuinely provides is tamper-evidence and a shared, append-only audit trail
across mutually untrusting parties, not truth. Incorrect data written to a ledger stays
wrong forever, just verifiably and immutably wrong. This is the Oracle problem: on-chain logic
cannot itself verify an off-chain fact; it can only faithfully record whatever an oracle feeds
it.

Sustainability varies enormously by consensus mechanism: proof-of-work chains consume far more
energy than proof-of-stake chains, which in turn consume far more than permissioned or
BFT-style consensus among a small known set of validators. Energy figures quoted for one
consensus mechanism (for example, post-transition Ethereum) do not generalize to others.

Two genuine, unresolved tensions recur in every design: transparency (auditability) versus
confidentiality (commercially or contractually sensitive payload data), usually resolved by
anchoring only a hash or commitment on-chain while keeping the actual payload off-chain; and
decentralization versus control, where more decentralization typically means slower governance
and harder error correction, not a strictly better outcome.

When judging whether data belongs on a blockchain versus a conventional database, weigh
whether the data genuinely needs a tamper-evident record across parties who do not trust each
other's databases, whether the write frequency can tolerate consensus latency and cost, and
whether there is a real, verifiable off-chain-to-on-chain integrity binding, rather than
treating "it's on a blockchain" as self-evidently more trustworthy.
