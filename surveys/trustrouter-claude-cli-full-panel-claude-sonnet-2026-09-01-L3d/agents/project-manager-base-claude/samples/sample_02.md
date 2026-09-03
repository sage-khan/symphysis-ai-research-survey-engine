# Sample 3 of 3

- Best: A_insider
- Worst: A_sybil

## Stated reasoning (submitted with the answer)

In the reference setting (a permissioned/consortium-style network among known, vetted stakeholders -- owner, contractor, insurers, authorities -- rather than an open public chain), insider resistance is the most consequential attack-resistance sub-dimension: the realistic threat to construction-data integrity is a legitimate, credentialed party (site engineer, inspector, contractor admin) altering or backdating records they are authorized to touch -- e.g. falsifying an inspection report or compliance certificate -- which is exactly the kind of dispute construction project managers actually encounter (the questionnaire's own Q-A6 asks about observed disputes over construction-data integrity, which in my experience are overwhelmingly insider-driven rather than external spoofing). Oracle resistance matters but only for the subset of on-chain data fed by IoT sensors or monitoring devices (structural health monitoring, energy meters); a large share of construction documentation (permits, certificates, BIM deliverables, contracts) is human-entered rather than oracle-fed, so tampering there is a narrower, though real, concern -- hence it sits in the middle. Sybil resistance is the weakest driver of routing decisions in this context because construction blockchain deployments are typically permissioned consortiums with KYC-style onboarding of named institutional participants, not open networks where anyone can mint throwaway identities; the attack surface for fabricating many fake identities to out-vote honest nodes is comparatively low relative to a single insider abusing already-legitimate access. My best-to-others and others-to-worst ratings (1/3/6 and 6/2/1) are set to be mutually consistent (3x2=6, matching the direct 6x insider-to-sybil gap) rather than arbitrary. This ranking is a professional judgement call built on general construction-industry experience with data disputes and typical consortium-blockchain architecture assumptions, not a figure drawn directly from the provided glossary excerpt, which defines the three sub-parts but does not itself rank them.

## Sources cited

shared knowledge: trustrouter_expert_questionnaire_v5_real_survey_instrument.md, general_knowledge (all claims verified genuine)
