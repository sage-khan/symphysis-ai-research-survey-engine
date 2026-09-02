# Sample 1 of 3

- Best: T_chain
- Worst: T_history

## Stated reasoning (submitted with the answer)

For polyglot-persistence routing decisions on construction data, the integrity of the custody chain (T_chain) is the most critical factor. In data engineering practice, custody-chain verification is the primary technical evidence of whether data can be trusted for on-chain storage or other persistence modes. Even data from highly credentialed sources (T_source) can be corrupted or tampered with during transmission and handling; conversely, a verified, intact chain provides direct evidence that a specific data instance is trustworthy, regardless of source credentials. This makes T_chain approximately 3× more important than T_source for routing decisions. Historical track record (T_history) is least important because it is backward-looking and does not guarantee this instance's integrity. A source with perfect historical reliability can still produce compromised data in this instance. Past performance is a confidence signal, but in data governance for blockchain or hybrid storage, actionable evidence of current integrity outweighs aggregate historical confidence. T_source is approximately 2× more important than T_history because source identity and credibility are directly verifiable and required for data governance compliance and lineage tracking, whereas history is merely predictive. The custody chain is approximately 5× more important than history—the immediate technical evidence of integrity is far more decisive than aggregate past performance when deciding whether to commit data to immutable ledgers.

## Sources cited

shared knowledge: trustrouter_expert_questionnaire_v5_real_survey_instrument.md, general_knowledge (all claims verified genuine)
