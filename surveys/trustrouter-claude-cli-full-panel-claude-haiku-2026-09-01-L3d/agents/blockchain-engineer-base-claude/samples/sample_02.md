# Sample 3 of 3

- Best: A_insider
- Worst: A_sybil

## Stated reasoning (submitted with the answer)

In a permissioned-ledger deployment storing construction records, the three attack vectors have sharply different threat profiles. A_sybil (fake identities) is the least important because permissioned blockchains inherently solve this at the enrollment and access-control layer—you do not grant network access to unverified entities, so Sybil attacks cannot originate from within the consensus layer. A_oracle (device/sensor tampering) is moderately important; it matters for construction data that includes sensor readings (environmental monitoring, material testing devices, structural health sensors), but not all construction records depend on sensor data. Some records are pure attestations or documentation from trusted professionals, where oracle attacks are irrelevant. A_insider (malicious legitimate access) is most critical. In permissioned systems, the real threat surface is a participant with valid credentials—a contractor, inspector, or site manager—attempting to falsify or tamper with records. This cannot be prevented by the permissioning mechanism itself (which grants them legitimate access) and requires strong cryptographic evidence, audit trails, and technical controls within the blockchain itself. From a production perspective on permissioned ledgers, insider attacks are the most likely and hardest to defend against technically. The multiplicative structure of TrustRouter means any weakness in A directly reduces overall trust; given the ranking, A_insider drives that factor most heavily. The 7:3:1 ratio between insider:oracle:sybil reflects that insider resistance is the technical bottleneck, oracle resistance applies to a subset of record types, and Sybil resistance is largely delegated to identity infrastructure upstream of the blockchain.

## Sources cited

shared knowledge: trustrouter_expert_questionnaire_v5_real_survey_instrument.md, general_knowledge (all claims verified genuine)
