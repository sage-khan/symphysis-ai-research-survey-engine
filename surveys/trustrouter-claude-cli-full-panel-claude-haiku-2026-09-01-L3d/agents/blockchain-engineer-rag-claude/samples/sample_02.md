# Sample 3 of 3

- Best: A_insider
- Worst: A_sybil

## Stated reasoning (submitted with the answer)

For construction data routed on permissioned ledgers, insider resistance (A_insider) is the primary attack surface and most critical dimension. In permissioned systems with pre-enrollment identity verification, Sybil attacks are substantially mitigated at the governance layer—all participants are consortium-vetted before joining, making the 'fake-identity problem' a negligible threat compared to legitimate parties with actual system access. This aligns with Vaziry et al. (2024), which frames both Sybil and Insider threats as instances of the 'who is really behind this identity' question, but in permissioned contexts the insider variant dominates because identities are already pre-established. Insider resistance directly addresses the most realistic and damaging attack vector: a legitimate engineer, inspector, project manager, or contractor with genuine system access falsifying or tampering with construction records (specifications, inspection reports, change orders, measurements). Oracle resistance (A_oracle) ranks second. Construction data relies heavily on external measurements, sensor readings, and inspection records that must be attested before use on-chain. Astraea (Adler et al., 2018) establishes that the oracle problem—trusting external real-world facts—is a fundamental, hard problem in blockchain systems, and construction's dependence on sensor data and off-chain evidence makes this significant. However, oracle resistance is somewhat orthogonal to ledger design itself; it is addressed through external verification mechanisms and data-source governance rather than being intrinsic to the ledger's attack resistance. Sybil resistance is rated least important: pre-enrollment in permissioned ledgers makes the digital-physical identity-mapping problem (Vaziry et al., 2024) far less acute than in open systems. The ratio 7:4:1 (insider:oracle:sybil) reflects the relative threat magnitudes in production permissioned-ledger contexts for construction-project data.

## Sources cited

blockchain_trust_and_attack_resistance.md, general_knowledge (all claims verified genuine)
