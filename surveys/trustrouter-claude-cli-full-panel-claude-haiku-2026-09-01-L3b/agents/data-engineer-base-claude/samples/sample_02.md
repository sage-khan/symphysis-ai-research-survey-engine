# Sample 3 of 3

- Best: T_chain
- Worst: T_history

## Stated reasoning (submitted with the answer)

As a data engineering specialist responsible for polyglot-persistence routing, my judgment prioritizes custody-chain integrity as the single most critical factor for construction data destined for blockchain storage. This reasoning is rooted in the irreversibility principle: blockchain is immutable by design, meaning any data corruption before storage becomes permanent and unrecoverable. The custody chain is the only mechanism that provides real-time, deterministic verification of whether specific data has been tampered with en route from creation to submission. Once data is on-chain, no amount of source credibility or historical track record can retroactively correct corruption. For routing decisions (full on-chain vs. hybrid vs. conventional storage), chain integrity is therefore the gating factor: if the custody chain is compromised, the data is unsuitable for immutable storage regardless of other factors. T_source (source credentials) ranks second: knowing and trusting the authoring organization is a prerequisite for baseline confidence, but source verification alone is insufficient—a trusted source can have one specific dataset corrupted. T_history (historical track record) ranks third: while useful for probabilistic confidence, it is predictive rather than deterministic about this submission, and new sources (common in construction projects) may have no history at all, yet the other two factors still apply. In construction contexts with long asset lifecycles (as noted in the reference scenario), the integrity of data entering permanent records is non-negotiable; custody-chain evidence is the only mechanism that prevents storing corrupted data on immutable ledgers. The multiplicative nature of trust (per the TrustRouter model cited in the survey structure) means chain failure is a critical path failure: broken chain zero-outs all other trust factors.

## Sources cited

shared knowledge: trustrouter_expert_questionnaire_v5_real_survey_instrument.md, general_knowledge (all claims verified genuine)
