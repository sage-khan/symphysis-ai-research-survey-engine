# Sample 2 of 3

- Best: A_oracle
- Worst: A_sybil

## Stated reasoning (submitted with the answer)

In permissioned-ledger deployments for construction data, oracle resistance (sensor and device tampering) is the most critical attack vector. Permissioned systems mitigate sybil attacks at the governance layer through identity vetting, role-based access control, and KYC during onboarding—fake identities cannot be injected into a system with explicit participant approval. However, oracle attacks exploit the inherent weakness in any blockchain system: cryptographic tamper-evidence cannot fix poisoned inputs. Construction data originates heavily from sensors, IoT devices, and on-site measurements. If these sources are compromised or miscalibrated, the on-chain record becomes a ledger of false data, rendering blockchain's audit trail meaningless. This is the primary technical failure mode unique to blockchain adoption. Insider resistance (malicious legitimate access) ranks second—it is a real governance and procedural risk that cannot be solved by cryptography alone—but it remains more tractable than oracle attacks because it requires an adversary to already possess valid credentials, and procedural controls, multi-signature schemes, and audit trails can detect or prevent many insider attacks. Sybil resistance ranks last because permissioned systems have already solved the identity problem upstream; it is a governance achievement, not a technical ledger property that should influence routing decisions. This ranking reflects the practical risk hierarchy facing a blockchain/DLT engineer evaluating whether to commit construction-project data to on-chain storage: the decision hinges on whether input integrity can be assured, not on whether the ledger can track multiple fake identities (it cannot) or detect insider misuse (governance handles that).

## Sources cited

shared knowledge: trustrouter_expert_questionnaire_v5_real_survey_instrument.md, general_knowledge (all claims verified genuine)
