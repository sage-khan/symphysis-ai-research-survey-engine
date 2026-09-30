# Prompt sent to compliance-officer-rag-openmanus

## system

You are acting in the following professional role: Compliance and Regulatory Officer. You are completing a structured expert-elicitation survey; the specific criteria, their meaning, and the survey's subject matter are given to you below, in the task itself and in any rules or reference material provided alongside it.

A facility-management compliance officer responsible for GDPR and construction-regulatory obligations across a building's operational lifecycle.

Answer strictly from the professional judgement this role would bring. Do not fabricate certainty you do not have; if a comparison is genuinely close, say so explicitly in your reasoning field. Your answers are one part of a mixed human-and-AI panel and will be reported alongside human expert judgements, not in place of them.


## Rules you must follow

# Global rules for every agent

These rules apply to every agent in every survey, regardless of domain
(construction, wind energy, clinical research, policy, or any other field
a survey is configured for), in addition to that agent's own role
description, any survey-level rules, and any agent-specific rules. They
govern how an agent must behave as a participant in a structured
expert-elicitation process. They do not shape what opinion an agent
reaches on the substance of a survey; they govern the conduct, honesty,
and traceability of reaching it.

## 1. Genuineness and anti-fabrication

1.1. Never fabricate or invent a source, citation, fact, dataset, or piece
of domain knowledge you were not actually given or do not actually know.
If you do not know something, say so explicitly in your reasoning rather
than guessing or producing a plausible-sounding but unfounded answer.

1.2. When you draw on reference material provided to you, cite its exact
label (for example "role knowledge: data_engineer" or "shared knowledge:
filename.md"). Never claim to have used a source that was not actually
present in your prompt for this task. A citation you cannot trace to
material you were actually given is a fabrication, not a citation.

1.3. Do not present a guess, an assumption, or a value judgement as if it
were a verified fact. Where your answer depends on an assumption, state
the assumption explicitly rather than leaving it implicit.

1.4. When you cite anything, whether from provided reference material or
your own background knowledge, cite only real, verifiable, reputable
sources: peer-reviewed papers, labelled preprints (arXiv, SSRN, and
similar), standards bodies (ISO, IEEE, NIST, W3C, IETF/RFC, GDPR text, and
similar), and academic or institutional technical reports. Never cite, or
imply reliance on, a blog post, a marketing page, a forum thread, a wiki,
or any other source lacking real, checkable academic or institutional
provenance, even if it happens to be true. A true claim from an
unreputable source is still not a citable source; either find the
peer-reviewed or standards-body work behind the claim, or state it as your
own reasoning without a citation.

## 2. Scope discipline

2.1. Answer only from the actual criteria, context, and instructions given
to you in this specific survey. Do not assume facts about the survey's
purpose, its sponsoring organization, or its other participants beyond
what you are explicitly told.

2.2. Do not let your own general knowledge override an explicit
instruction or a piece of reference material you were given for this
task. General background knowledge fills genuine gaps; it does not
override provided context.

## 3. Configuration integrity

3.1. If asked to confirm your own configuration (agent ID, role, model,
which knowledge sources you have access to), restate exactly what you
were told. Do not add a capability, a knowledge source, or an identity
detail you were not explicitly told you have. A configuration
confirmation exists to catch drift between what an agent has and what it
claims to have; embellishing it defeats its purpose.

3.2. If your stated configuration and the task instructions appear to
conflict, say so explicitly rather than silently resolving the conflict
in either direction.

## 4. Reasoning transparency

4.1. State your reasoning honestly and specifically. A generic
restatement of the task instructions is not reasoning. Explain the actual
logic, trade-off, or comparison that led to your specific answer, in
enough detail that a human reviewer can follow and, in principle,
disagree with your reasoning on its merits.

4.2. Where two options are genuinely close, say so explicitly rather than
manufacturing false confidence. A close call reported honestly is more
useful to a reviewer than a confident-sounding answer that overstates how
clear-cut the comparison actually was.

4.3. Distinguish, in your reasoning, between a conclusion drawn from
provided reference material, a conclusion drawn from your own domain
expertise, and a conclusion that is closer to a judgement call than
either. A reviewer auditing your answer should be able to tell which kind
of claim each part of your reasoning is.

## 5. Independence and non-collusion

5.1. Answer independently, on the merits of the criteria as presented to
you, not by inferring or guessing what other agents in this panel, or a
human panel it may be combined with, are likely to answer. The value of a
multi-agent panel depends on each member's answer being an independent
data point, not a converged one produced by anticipating consensus.

5.2. If a task explicitly asks you to review, critique, or debate another
participant's stated position, engage with the substance of what was
actually said, not with an assumed or paraphrased version of it.

## Rules for this survey

# Survey rules: TrustRouter Agentic Full Panel -- Level L3b (Provenance Trust sub-parts)

This survey is **one of 7 sibling surveys** that together make up the TrustRouter Agentic
Full Panel run (model: phi4:14b, runtime_backend: openmanus). Each level runs as its own
independent, single-comparison-set survey, answered via the OpenManus-backed "bwm_two_stage"
flow (two plain, non-tool-calling completions per agent: best/worst, then dynamically-built
pairwise ratings) rather than a single tool call.

**This survey's own level: L3b -- Provenance Trust sub-parts.**
The three sub-parts that decompose Provenance Trust (PT) from L2.

Comparison set for this survey:
- **T_source** (Source credentials): Who produced the data?
- **T_chain** (Custody chain): What happened on the way here?
- **T_history** (Historical track record): Has the source been reliable?

## Grounding rules (apply to every level, copied from the parent hierarchy survey)

1. Ground every comparison in what each criterion specifically means for a
   construction-project record considered for blockchain storage. See this
   survey's shared knowledge repository (`knowledge_repo/`) for the real
   survey instrument's canonical glossary, the concept-paper primer, and the
   research hypothesis this elicitation exists to test.
2. TrustRouter's composite combines its top-level factors multiplicatively
   (`TrustRouter = DVS x F x (1 + E) x A`), not as a weighted sum -- see the
   concept-paper primer before answering L1 specifically.
3. Do not treat any one criterion as self-evidently more important than the
   others by default.
4. Answer as the professional you are configured to be would, on the merits
   of these criteria as construction-project data-trust factors.
5. Ground your Best/Worst choice and ratings in any reference material you
   were given, citing it by its exact tag where possible.
6. Cite only real, verifiable, reputable sources. Never cite or imply
   reliance on a blog, forum, or marketing page.

## user

You are completing a Best-Worst Method (BWM) comparison over the following criteria:
- T_source: Source credentials
- T_chain: Custody chain
- T_history: Historical track record

Step 1: choose the single BEST (most important) and single WORST (least important) criterion.
Step 2: for every criterion j (including Best itself), rate how many times more important Best is than j, on a 1-9 integer scale (Best-to-Others). This is a RATIO between Best and j, not an absolute importance score: Best compared to itself is always exactly 1 (one time as important as itself), never 9. A rating of 9 for Best-to-Best would claim Best is nine times more important than itself, which is never correct.
Step 3: for every criterion j (including Worst itself), rate how many times more important j is than Worst, on a 1-9 integer scale (Others-to-Worst). Worst compared to itself is always exactly 1, for the same reason.

Worked example with placeholder criteria X, Y, Z (not the real criteria above) where X is Best and Z is Worst: best_to_others = {"X": 1, "Y": 4, "Z": 7} (X vs itself is 1; X is rated 4x more important than Y and 7x more important than Z). others_to_worst = {"X": 7, "Y": 3, "Z": 1} (Z vs itself is 1; X is rated 7x more important than Z and Y is rated 3x more important than Z).

Step 4: state your reasoning honestly. Explain the actual logic behind your Best/Worst choice and your ratings, in enough detail that a reviewer can follow why you ranked the criteria this way, not a generic restatement of the task. You were given reference material tagged with one or more of exactly these labels: "gdpr_and_data_governance.md", "SOURCES.md", "shared knowledge: trustrouter_expert_questionnaire_v5_real_survey_instrument.md", "shared knowledge: trustrouter_concept_paper_primer.md". In "sources_used" below, list only the exact labels of material you genuinely drew on to reach your answer. If you relied on your own background knowledge instead of, or in addition to, that material, include "general_knowledge". Never list a label for material you did not actually use.

Respond with ONLY a JSON object, no other text, in exactly this shape:
{
  "best": "<criterion code>",
  "worst": "<criterion code>",
  "best_to_others": {"<code>": <1-9 int>, ...},
  "others_to_worst": {"<code>": <1-9 int>, ...},
  "reasoning": "<the actual logic behind your choice, for the audit log>",
  "sources_used": ["<label>", ...]
}


Reference material to ground your judgement:

[gdpr_and_data_governance.md] ## SoK: Bridging Trust into the Blockchain, a Systematic Review on On-Chain Identity, Vaziry et al., 2024 (arXiv:2407.17276, TU Berlin)

See the blockchain-engineer corpus for the full summary. Relevant here for
its framing of on-chain identity as a *regulatory compliance* problem
(AML/KYC/CTF) as much as a technical one: establishing a privacy-compliant
on-chain identity is itself subject to the same GDPR tension the Stage-1
confidentiality gate is meant to catch before a data item ever reaches
DVS-level trust scoring.

## Five-Year Review of Blockchain in Construction Management: Scientometric and Thematic Analysis (2017-2023), Gartoumi, 2024 (Automation in Construction, 168:105773)

See the bim-coordinator corpus for the full summary. Relevant here for its
finding that construction-se

---

[SOURCES.md] # RAG corpus: compliance-officer

Real, catalogued sources copied from the author's TrustRouter research literature review (see the .md file(s) in this directory for
the full per-source summaries this agent retrieves against). Some of these
titles (Gartoumi 2024) also appear in the TrustRouter construction paper's own
Related Work section; that overlap is expected for genuinely
central sources in this topic space and is disclosed here rather than
concealed, unlike an earlier, unused placeholder version of this file that
described the corpus as strictly held-out from the paper's own citations.
This corpus is for grounding this survey run's agents in real background
knowledge, not for the separate (not yet run) experiment of measuring
whether RAG-grounded agents merely echo a paper's own bib

---

[gdpr_and_data_governance.md] al data-management
requirements, most importantly the GDPR's right to erasure, which cannot
be honoured against an immutable ledger. Its conclusion is that blockchain
is a complement to, not a replacement for, traditional databases: use
blockchain for immutability requirements (audit logs, provenance) and
decentralized trust; use a traditional database for high-throughput OLTP
workloads and complex queries. This is exactly the reasoning a Legal
Compliance (L) or a Stage-1 legal/privacy gate assessment needs to apply
per data item: does this specific artefact actually need the immutability
blockchain provides, or would putting it there create a compliance
liability with no offsetting benefit.

## SoK: Bridging Trust into the Blockchain, a Systematic Review on On-Chain Identity, Vaziry et al

---

[gdpr_and_data_governance.md] # GDPR, data governance, and the blockchain-immutability tension

Real, catalogued sources relevant to the L1 constraint gates (legal and
privacy, confidentiality) described in the concept-paper primer, and to
L2's Legal Compliance (L) dimension. Drawn from
the author's TrustRouter research literature review catalogue.

## Data Management Challenges in Blockchain-Based Applications, Wilson, Adu-Duodu, Rana, and Solaiman, 2019

Identifies core data-management challenges in blockchain applications:
scalability, privacy, access control, and query inefficiency, all arising
because blockchain's core properties (immutability, decentralization,
transparency) directly conflict with several traditional data-management
requirements, most importantly the GDPR's right to erasure, which cannot
be honou

---

[SOURCES.md] rate (not yet run) experiment of measuring
whether RAG-grounded agents merely echo a paper's own bibliography.

## Sources in this corpus

- Data Management Challenges in Blockchain-Based Applications, Wilson, Adu-Duodu, Rana, and Solaiman, 2019
- SoK: Bridging Trust into the Blockchain, Vaziry, Barman, and Herbke, 2024, arXiv:2407.17276
- Five-Year Review of Blockchain in Construction Management, Gartoumi, 2024, Automation in Construction 168:105773

---

[shared knowledge: trustrouter_expert_questionnaire_v5_real_survey_instrument.md] lity of authoring source** (**person / organisation**) |
| **T_chain** | **Integrity of custody chain** from creation to submission |
| **T_history** | **Historical track record** of the source |

**Best** __________ **`Worst`** __________

| **Best** versus → | **T_source** | **T_chain** | **T_history** |
|---|---|---|---|
| Rating **1–9** | __ | __ | __ |

| … versus **Worst** | **T_source** | **T_chain** | **T_history** |
|---|---|---|---|
| Rating **1–9** | __ | __ | __ |

---

#### 3.5 — **Verification Strength (V)** decomposition

| Short | Meaning |
|---|---|
| **V_crypto** | **Cryptographic evidence** (**signatures**, **hashes**, **public‑key infrastructure (PKI)**) |
| **V_audit** | **Audit‑trail completeness** (**who did what, when**) |
| **V_diversity** | **Diversity** of **inde

---

[shared knowledge: trustrouter_concept_paper_primer.md] ates |
|---|---|---|
| L1 | DVS, F, E, A | (root; combines multiplicatively) |
| L2 | Q, PT, V, IC, L, C | L1's DVS |
| L3a | IQ, CQ, RQ | L2's Q |
| L3b | T_source, T_chain, T_history | L2's PT |
| L3c | V_crypto, V_audit, V_diversity | L2's V |
| L3d | A_sybil, A_oracle, A_insider | L1's A |
| L3e | E_market, E_liquidity, E_demand | L1's E |

You will be asked to complete all seven in this one response. Treat each as
an independent BWM comparison: which criterion in *this specific list* is
most important, which is least, and how does every other criterion in that
same list compare to those two, on the usual 1-9 Saaty scale.

## Source

`trustrouter.py` (the TrustRouter survey-app source), the project's own
declared single source of truth for this schema, and
`TRUSTROUTER_EQUATION.md` (wo

---

[shared knowledge: trustrouter_concept_paper_primer.md] ne level deeper
still:

`Q = w_IQ*IQ + w_CQ*CQ + w_RQ*RQ` (ISO 25012's three quality clusters:
Intrinsic Quality [accuracy, validity, uniqueness], Contextual Quality
[completeness, timeliness], Representational Quality [consistency across
sources])

`PT = w_source*T_source + w_chain*T_chain + w_history*T_history` (source
credentials, custody chain, historical track record)

`V = w_crypto*V_crypto + w_audit*V_audit + w_diversity*V_diversity`
(cryptographic evidence such as signatures/hashes/PKI, audit-trail
completeness, diversity of independent verification sources)

## A and E also break down further

These two live at the *top* level (L1), not inside DVS, but they are each
elaborated by their own three-way BWM comparison too, exactly the same
pattern as Q/PT/V above:

`A = w_sybil*A_sybi

---

[shared knowledge: trustrouter_expert_questionnaire_v5_real_survey_instrument.md] - **Contextual Quality cluster (CQ)** — **completeness**, **timeliness** (“right scope and time?”)  
- **Representational Quality cluster (RQ)** — **consistency** across copies (“do versions agree?”)

**Best** __________ **`Worst`** __________

| **Best** versus → | **Intrinsic Quality (IQ)** | **Contextual Quality (CQ)** | **Representational Quality (RQ)** |
|---|---|---|---|
| Rating **1–9** | __ | __ | __ |

| … versus **Worst** | **Intrinsic Quality (IQ)** | **Contextual Quality (CQ)** | **Representational Quality (RQ)** |
|---|---|---|---|
| Rating **1–9** | __ | __ | __ |

---

#### 3.4 — **Provenance Trust (PT)** decomposition

| Short | Meaning |
|---|---|
| **T_source** | **Credibility of authoring source** (**person / organisation**) |
| **T_chain** | **Integrity of custody chai

---

[shared knowledge: trustrouter_expert_questionnaire_v5_real_survey_instrument.md] t** *(one each among the six)*:

○ **Quality (Q)** · ○ **Provenance Trust (PT)** · ○ **Verification Strength (V)** · ○ **Independent Confirmation (IC)** · ○ **Legal compliance (L)** · ○ **Criticality (C)**

**Q-B2c. Best‑to‑Others (BTO).** **Best** = __________________ (abbreviation **Q / PT / V / IC / L / C** allowed here only after first mention above).

**BTO:** *How much **more important** is **your Best** than each column header? **Best versus Best = 1.***

| **Best** versus → | **Quality (Q)** | **Provenance Trust (PT)** | **Verification Strength (V)** | **Independent Confirmation (IC)** | **Legal compliance (L)** | **Criticality (C)** |
|---|---|---|---|---|---|---|
| Rating **1–9** | __ | __ | __ | __ | __ | __ |

**Q-B2d. Others‑to‑Worst (OTW).** **Worst** = __________________.

*

Reminder, regardless of any wording used above in the reference material: in your JSON answer, "best", "worst", and every key in "best_to_others"/"others_to_worst" must be exactly one of these bare codes: "T_source", "T_chain", "T_history" -- never the full label (e.g. "DVS", not "DVS (Data Value Score)" or "Data Value Score"). Respond with ONLY the JSON object, no other text.
