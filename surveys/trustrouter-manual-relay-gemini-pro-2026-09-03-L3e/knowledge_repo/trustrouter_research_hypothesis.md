# TrustRouter's research hypothesis

Extracted, not paraphrased beyond trimming, from the TrustRouter construction
research paper's own stated research gap and contribution
(`trustrouter_construction_researchpaper.tex`, "Research Gap" and "Our
Contribution" subsections, from the author's broader TrustRouter research).
This is the actual hypothesis the weight elicitation you are completing
exists to calibrate, not a restatement written for this survey.

## The gap this framework claims to close

No published framework, whether framed as a blockchain-adoption decision
tool or as a Digital Building Logbook architecture, provides a
mathematically grounded decision procedure that treats legal, privacy, and
technical constraints as non-negotiable eligibility conditions applied
before multi-dimensional trust assessment, rather than as criteria averaged
alongside it. Existing approaches typically rely on weighted scoring models
in which all criteria are aggregated into a single evaluation score. As a
result, data that violate critical legal requirements, exceed technical
limitations, or fail confidentiality constraints may still receive
favorable blockchain recommendations if they perform well in other
dimensions, a failure mode that is particularly consequential in
construction, where regulatory compliance, data sovereignty requirements,
and large-scale digital assets such as Building Information Models impose
strict operational constraints.

## The hypothesis, stated as three requirements

Answering this gap requires:

1. A hard-gate mechanism that excludes non-compliant data before scoring,
   rather than averaging compliance into the score.
2. A multi-dimensional trust model whose weights are calibrated through a
   documented construction-expert elicitation rather than assigned
   arbitrarily. **This is the part your Best-Worst Method comparisons in
   this survey directly test**: TrustRouter's claim only holds if real
   domain experts (human and, in this panel, agent) actually converge on
   the relative importance it proposes for DVS/F/E/A and their
   sub-criteria, rather than the weights being an arbitrary modeling
   choice.
3. An explicit mapping from the resulting suitability score to one of the
   storage routes a polyglot construction data architecture must actually
   choose among (BLOCKCHAIN, IPFS_HASH, OFFCHAIN).

## What TrustRouter claims as its novelty

The first framework to make the constraint-then-score decision an
unconditional, pre-scoring gate rather than a criterion averaged into the
evaluation, and the first to close this gap for construction data
specifically by calibrating its trust weights against a documented
construction-expert elicitation. Its claimed novelty is this combination,
not any one element in isolation: constraint-gating, multi-dimensional
trust scoring, and threshold-based storage routing each have precedent
elsewhere, but (per the paper's own literature review) no prior
blockchain-adoption tool or Digital Building Logbook architecture, BUILDCHAIN
included, assembles all three into one deployable, auditable pipeline.

## Why your answer matters to this hypothesis

You are not just producing a number for a report. Your Best/Worst choices
and ratings are part of the actual evidence the paper needs to support (or
fail to support) requirement 2 above. Answer from genuine professional
judgement about these specific criteria, not from a guess at what the
paper's authors want to hear.
