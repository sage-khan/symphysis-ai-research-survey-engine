# Sample 2 of 3

- Best: T_source
- Worst: T_history

## Stated reasoning (submitted with the answer)

From a compliance-officer lens, Provenance Trust for a construction record ultimately has to answer 'who is legally accountable for this data and can that accountability be established.' T_source (source credentials) does that directly: a signed report from a chartered structural engineer or a licensed authority is what building codes, professional-liability regimes, and GDPR's data-controller/processor identification requirements actually key on (per shared knowledge: trustrouter_expert_questionnaire_v5_real_survey_instrument.md, PT's example is precisely 'signed report from a chartered structural engineer'). Without a credentialed, identifiable source, neither a clean custody chain nor a good historical record has much regulatory weight, since there is no accountable party to attach compliance obligations to. T_chain (custody chain) I rank second: chain-of-custody integrity is a recognised evidentiary concept and matters for tamper-evidence and audit-trail admissibility, but it is a control on top of an already-identified source rather than a substitute for one -- a pristine custody chain for an anonymous or unqualified originator still leaves compliance exposure. T_history (historical track record) I rank lowest: it is a reputational/statistical heuristic -- useful corroboration -- but it is not itself a formal regulatory or legal criterion, is harder to verify objectively, and can be gamed or simply unavailable for new-but-properly-credentialed sources, so it should not be weighted as heavily as either the source's formal credentials or the procedural integrity of custody. I set best_to_others and others_to_worst to be internally consistent (T_source:T_chain=2, T_chain:T_history=2, T_source:T_history=4=2x2) since these are genuinely on a graduated scale rather than sharply separated tiers -- the T_source vs T_chain gap in particular is a closer call than the gap to T_history, and I want to flag that explicitly rather than overstate confidence in ranking credentials far above chain-of-custody.

## Sources cited

shared knowledge: trustrouter_expert_questionnaire_v5_real_survey_instrument.md, general_knowledge (all claims verified genuine)
