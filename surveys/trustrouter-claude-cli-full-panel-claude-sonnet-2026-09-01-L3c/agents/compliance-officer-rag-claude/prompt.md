# Prompt sent to compliance-officer-rag-claude

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

# Survey rules: TrustRouter Claude CLI Panel -- Level L3c (Verification Strength sub-parts)

This survey is **one of 7 sibling surveys** that together make up the TrustRouter Claude CLI
Panel run (model: sonnet, provider: claude_cli, runtime_backend: direct_completion). Each
level runs as its own independent, single-comparison-set survey, answered via a single
structured-JSON completion (the flat "bwm" instrument), not the two-turn agentic flow used for
the local SLM phases.

**This survey's own level: L3c -- Verification Strength sub-parts.**
The three sub-parts that decompose Verification Strength (V) from L2.

Comparison set for this survey:
- **V_crypto** (Cryptographic evidence): Signatures, hashes, PKI.
- **V_audit** (Audit trail completeness): Who did what, when.
- **V_diversity** (Diversity of verification sources): Multiple independent parties.

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
- V_crypto: Cryptographic evidence
- V_audit: Audit trail completeness
- V_diversity: Diversity of verification sources

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

[gdpr_and_data_governance.md] the bim-coordinator corpus for the full summary. Relevant here for its
finding that construction-sector blockchain adoption has grown for five
years without the industry developing rigorous decision criteria for
when blockchain storage is legally and practically appropriate, the
governance gap the constraint-gate stage is designed to close before any
weighted trust score is even computed.

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

[shared knowledge: trustrouter_expert_questionnaire_v5_real_survey_instrument.md] **Legal** and **privacy** suitability for **immutable** archiving | | | | |
| **Confidentiality** / **competitive sensitivity** | | | | |
| **Technical practicality** versus realistic **permissioned‑ledger** limits | | | | |

If **no gate is marked Fail** (**Borderline** still allows continuation), score **each** field independently **[0.00 , 1.00]** (**do not** force the nine numbers to **sum** to **1**).

| Field | Score **0–1** | Guidance |
|---|---|---|
| **Quality (Q)** | _____ | Structural–technical fidelity of the dossier |
| **Provenance Trust (PT)** | _____ | Authority + custody story |
| **Verification Strength (V)** | _____ | Signatures / logs |
| **Independent Confirmation (IC)** | _____ | Independent corroboration depth |
| **Legal compliance (L)** | _____ | Regulatory / oblig

---

[shared knowledge: trustrouter_expert_questionnaire_v5_real_survey_instrument.md] **Audit‑trail completeness** (**who did what, when**) |
| **V_diversity** | **Diversity** of **independent verification** sources |

**Best** __________ **`Worst`** __________

| **Best** versus → | **V_crypto** | **V_audit** | **V_diversity** |
|---|---|---|---|
| Rating **1–9** | __ | __ | __ |

| … versus **Worst** | **V_crypto** | **V_audit** | **V_diversity** |
|---|---|---|---|
| Rating **1–9** | __ | __ | __ |

---

#### 3.6 — **Attack Resistance (A)** decomposition

| Short | Meaning |
|---|---|
| **A_sybil** | **Fake‑identity (“Sybil”)** submissions |
| **A_oracle** | **Tampering at the sensing / device (“oracle”)** interface |
| **A_insider** | **Malicious insider** with **legitimate credentials** |

**Best** __________ **`Worst`** __________

| **Best** versus → | **A_sybil** |

---

[shared knowledge: trustrouter_expert_questionnaire_v5_real_survey_instrument.md] hic** and **procedural** audit evidence | **Qualified electronic signature** dossier + tamper‑evident log |
| **IC** | **Independent Confirmation (IC)** | **Independent** cross‑checks (second party, second sensor set, etc.) | **Second independent audit** of the same quantities |
| **L** | **Legal compliance (L)** | Binding **regulatory** / **statutory** obligation attached to the datum | **Mandatory** building‑code or **energy performance** disclosure class |
| **C** | **Criticality (C)** | **Safety**, **financial**, or **contractual** impact if the datum is wrong | **Life‑safety** structural dependence (e.g. occupied **hospital** roof) |

**Q-B2a / b.** **Most important** · **Least important** *(one each among the six)*:

○ **Quality (Q)** · ○ **Provenance Trust (PT)** · ○ **Verification

---

[shared knowledge: trustrouter_expert_questionnaire_v5_real_survey_instrument.md] in aggregated or anonymised form. Data reside on institutional systems and are retained as required under applicable data-protection norms (normally up to seven years).

**Approval reference:** *[insert institutional ethics-committee approval number]*

**Study contacts:** *[insert email addresses]*

- [ ] I have read this information and freely agree to contribute.

---

## Background

Renewal-centric projects accumulate heterogeneous records (reports, **Building Information Modelling (BIM)**, inspections, metering, certifications). Subsequent actors must often rely on **integrity** — regulators, insurers, owners, and juridical oversight. Ordinary databases silently permit rewriting; **decentralised ledgers** improve **tamper‑evidence** (changes become detectable), but they are costly and

---

[shared knowledge: trustrouter_concept_paper_primer.md] **Q (Quality)**: is the data technically clean?
- **PT (Provenance Trust)**: can we trust who produced it?
- **V (Verification Strength)**: cryptographic or audit-trail evidence?
- **IC (Independent Confirmation)**: do multiple independent parties agree?
- **L (Legal Compliance)**: is this data required or regulated? (Distinct
  from the Stage-1 legal *gate*: a data item can pass the legal gate and
  still score anywhere on this dimension, e.g. "regulation requires this
  data to exist" is a different question from "regulation requires
  auditability of this specific record.")
- **C (Criticality)**: how big is the impact if it is wrong?

Two of these six are themselves broken down further, one level deeper
still:

`Q = w_IQ*IQ + w_CQ*CQ + w_RQ*RQ` (ISO 25012's three quality clusters:
Intri

Reminder, regardless of any wording used above in the reference material: in your JSON answer, "best", "worst", and every key in "best_to_others"/"others_to_worst" must be exactly one of these bare codes: "V_crypto", "V_audit", "V_diversity" -- never the full label (e.g. "DVS", not "DVS (Data Value Score)" or "Data Value Score"). Respond with ONLY the JSON object, no other text.
