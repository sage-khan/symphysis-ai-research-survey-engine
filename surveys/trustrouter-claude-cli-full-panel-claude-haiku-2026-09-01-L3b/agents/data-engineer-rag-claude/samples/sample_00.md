# Sample 1 of 3

- Best: T_chain
- Worst: T_history

## Stated reasoning (submitted with the answer)

For routing construction data to blockchain or hybrid storage, the integrity of the custody chain is the most critical factor. This follows from the data-engineering principle that audit logging and lineage tracking constitute the first-hand evidence for provenance trust; without a documented, unbroken custody chain, a data item's current state cannot be verified, regardless of source credentials or historical reliability. A known source (T_source) remains important but secondary—source credentials are necessary context, but they do not guarantee that a specific instance of data has not been altered, corrupted, or tampered with in transit. Historical track record (T_history) ranks worst because it is backward-looking and probabilistic; a historically reliable source can fail on any given submission, and conversely, past failures do not prevent a specific data item from being trustworthy if its chain is intact and its source is credible. From a data-pipeline perspective, the custody chain is the only contemporaneous evidence that the data matches its claimed provenance. Therefore T_chain is rated 7× more important than T_history (a large gap) and 5× more important than T_source (a moderate gap reflecting that source credentials matter but are overshadowed by chain integrity).

## Sources cited

data_quality_and_polyglot_persistence.md, shared knowledge: trustrouter_expert_questionnaire_v5_real_survey_instrument.md, general_knowledge (all claims verified genuine)
