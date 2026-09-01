# Prompt sent to blockchain-engineer-rag-openmanus

## system

You are acting in the following professional role: Blockchain / DLT Engineer. You are completing a structured expert-elicitation survey; the specific criteria, their meaning, and the survey's subject matter are given to you below, in the task itself and in any rules or reference material provided alongside it.

A blockchain/DLT engineer with production experience on permissioned-ledger deployments, responsible for evaluating technical feasibility, throughput, and tamper-evidence guarantees.

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

# Survey rules: TrustRouter Agentic Full Panel -- Level L2 (Six trust dimensions inside DVS)

This survey is **one of 7 sibling surveys** that together make up the TrustRouter Agentic
Full Panel run (model: phi4:14b, runtime_backend: openmanus). Each level runs as its own
independent, single-comparison-set survey, answered via the OpenManus-backed "bwm_two_stage"
flow (two plain, non-tool-calling completions per agent: best/worst, then dynamically-built
pairwise ratings) rather than a single tool call.

**This survey's own level: L2 -- Six trust dimensions inside DVS.**
The six trust dimensions that make up the Data Value Score (DVS) factor from L1.

Comparison set for this survey:
- **Q** (Quality): Is the data technically clean?
- **PT** (Provenance Trust): Can we trust who produced it?
- **V** (Verification Strength): Cryptographic or audit-trail evidence?
- **IC** (Independent Confirmation): Do multiple independent parties agree?
- **L** (Legal Compliance): Is this data required or regulated?
- **C** (Criticality): How big is the impact if it is wrong?

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
- Q: Quality
- PT: Provenance Trust
- V: Verification Strength
- IC: Independent Confirmation
- L: Legal Compliance
- C: Criticality

Step 1: choose the single BEST (most important) and single WORST (least important) criterion.
Step 2: for every criterion j (including Best itself), rate how many times more important Best is than j, on a 1-9 integer scale (Best-to-Others). This is a RATIO between Best and j, not an absolute importance score: Best compared to itself is always exactly 1 (one time as important as itself), never 9. A rating of 9 for Best-to-Best would claim Best is nine times more important than itself, which is never correct.
Step 3: for every criterion j (including Worst itself), rate how many times more important j is than Worst, on a 1-9 integer scale (Others-to-Worst). Worst compared to itself is always exactly 1, for the same reason.

Worked example with placeholder criteria X, Y, Z (not the real criteria above) where X is Best and Z is Worst: best_to_others = {"X": 1, "Y": 4, "Z": 7} (X vs itself is 1; X is rated 4x more important than Y and 7x more important than Z). others_to_worst = {"X": 7, "Y": 3, "Z": 1} (Z vs itself is 1; X is rated 7x more important than Z and Y is rated 3x more important than Z).

Step 4: state your reasoning honestly. Explain the actual logic behind your Best/Worst choice and your ratings, in enough detail that a reviewer can follow why you ranked the criteria this way, not a generic restatement of the task. You were given reference material tagged with one or more of exactly these labels: "blockchain_trust_and_attack_resistance.md", "SOURCES.md", "shared knowledge: trustrouter_expert_questionnaire_v5_real_survey_instrument.md", "shared knowledge: trustrouter_concept_paper_primer.md". In "sources_used" below, list only the exact labels of material you genuinely drew on to reach your answer. If you relied on your own background knowledge instead of, or in addition to, that material, include "general_knowledge". Never list a label for material you did not actually use.

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

[blockchain_trust_and_attack_resistance.md] # Blockchain trust, attack resistance, and the oracle problem

Real, catalogued sources relevant to the L1 Attack Resistance (A) factor and
its L3d breakdown (Sybil / Oracle / Insider resistance), and to L2's
Verification Strength (V) and Provenance Trust (PT) dimensions. Drawn from
the author's TrustRouter research literature review catalogue (never fabricated; each entry below is that catalogue's own
recorded content summary and findings for the cited source).

## Data trust framework using blockchain technology and adaptive transaction validation, Rouhani and Deters, 2021 (IEEE Access, DOI 10.1109/ACCESS.2021.3091327)

Proposes a comprehensive blockchain-based data trust framework for
trustworthy data sharing, implementing O'Hara's eight data trust
properties (discovery, provenance, acc

---

[SOURCES.md] # RAG corpus: blockchain-engineer

Real, catalogued sources copied from the author's TrustRouter research literature review (see the .md file(s) in this directory for
the full per-source summaries this agent retrieves against). Some of these
titles (Rouhani and Deters 2021, Konsta et al. 2023) also appear in the TrustRouter construction paper's own
Related Work section; that overlap is expected for genuinely
central sources in this topic space and is disclosed here rather than
concealed, unlike an earlier, unused placeholder version of this file that
described the corpus as strictly held-out from the paper's own citations.
This corpus is for grounding this survey run's agents in real background
knowledge, not for the separate (not yet run) experiment of measuring
whether RAG-grounded agent

---

[SOURCES.md] und
knowledge, not for the separate (not yet run) experiment of measuring
whether RAG-grounded agents merely echo a paper's own bibliography.

## Sources in this corpus

- Data trust framework using blockchain technology and adaptive transaction validation, Rouhani and Deters, 2021, DOI 10.1109/ACCESS.2021.3091327
- SoK: Bridging Trust into the Blockchain, Vaziry, Barman, and Herbke, 2024, arXiv:2407.17276
- A Survey of Trust Management for Internet of Things, Konsta, Lluch Lafuente, and Dragoni, 2023, DOI 10.1109/ACCESS.2023.3327335
- Astraea: Decentralized Blockchain Oracle, Adler, Berryhill, Veneris, et al., 2018

---

[blockchain_trust_and_attack_resistance.md] precisely the gap TrustRouter's
routing decision (as opposed to node reputation alone) addresses.

## Astraea: Decentralized Blockchain Oracle, Adler, Berryhill, Veneris, et al., 2018 (IEEE Cybermatics)

Proposes Astraea, a voting-game-based decentralized oracle for bringing
external facts onto a blockchain: "voters" make low-risk/low-reward random
propositions resistant to manipulation, while "certifiers" stake
high-risk/high-reward bets on outcomes. Directly relevant to A_oracle: the
oracle problem is that smart contracts can only act on data already on the
blockchain, so they need a trusted mechanism to attest to real-world facts
(sensor readings, off-chain events) before that data can be used on-chain,
exactly the attack surface A_oracle scores.

---

[blockchain_trust_and_attack_resistance.md] fication Strength (audit-trail completeness) and to how a trust score
can directly gate the cost/strength of the validation mechanism applied to
a piece of data, the same principle TrustRouter applies to storage-tier
routing rather than validator count.

## SoK: Bridging Trust into the Blockchain, a Systematic Review on On-Chain Identity, Vaziry et al., 2024 (arXiv:2407.17276, TU Berlin)

A systematisation-of-knowledge review (2,232 papers screened down to 13)
on establishing trusted, privacy-compliant on-chain identities for
regulatory compliance (AML/KYC/CTF), covering zero-knowledge proofs, PKI,
and web-of-trust mechanisms. Identifies two trust gaps directly relevant to
Insider and Sybil resistance: (1) trusting that an on-chain identity truly
represents the physical entity behind it (t

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

---

[shared knowledge: trustrouter_expert_questionnaire_v5_real_survey_instrument.md] ectrical, and Plumbing (MEP)**) engineer  
- Facility manager / compliance officer  
- **Blockchain** / **DLT** (**Distributed Ledger Technology (DLT)**) specialist  
- Researcher / lecturer (construction, BIM, **ICT** (**Information and Communication Technology (ICT)**), blockchain, analytics)  
- Doctoral or Master’s student — related topic  
- Other: ____________________

**Q-A2.** Years of relevant experience: **< 2 · 2–5 · 5–10 · > 10**

**Q-A3.** Highest completed education: Bachelor’s · Master’s · Doctorate (PhD) and/or professional licence (**PE**, Professional Engineer, **CEng**, Chartered Engineer, or equivalent): __________

**Q-A4.** Primary country or region of practice: ____________________

**Q-A5.** Familiarity **1–5** (1 = none, 5 = expert). One mark per row.

| Topic | 1

---

[shared knowledge: trustrouter_concept_paper_primer.md] a weighted
sum. Do not treat the L1 comparison as interchangeable with the others; it
answers "how much does getting this factor right matter to the overall
decision," not "what fraction of one total does this factor contribute."

The resulting score routes the data item to a storage tier:
`BLOCKCHAIN` at TrustRouter >= 0.80, `IPFS_HASH` between 0.60 and 0.80, and
`OFFCHAIN` below 0.60.

## DVS breaks down into six trust dimensions (the "gates, then a main
## formula, then each variable has its own formula" part)

`DVS = w_Q*Q + w_PT*PT + w_V*V + w_IC*IC + w_L*L + w_C*C`

Six lenses, this time genuinely combined as a weighted sum (this is the
level most previous survey runs stopped at):

- **Q (Quality)**: is the data technically clean?
- **PT (Provenance Trust)**: can we trust who produc

---

[shared knowledge: trustrouter_expert_questionnaire_v5_real_survey_instrument.md] _________________

**Q‑D4.** Any construct missing from **Quality (Q)**, **Provenance Trust (PT)**, **Verification Strength (V)**, **Independent Confirmation (IC)**, **Legal compliance (L)**, **Criticality (C)**, plus **Technical feasibility fit (F)**, **Economic Value (E)**, **Attack Resistance (A)**?

**Name:** __________________ **Why critical:** __________________ Acts as ○ **Gatekeeper** (**binary**) · ○ **Value multiplier** (**continuous score**).

**Q‑D5.** Rank adoption barriers (**1–5**, each digit once; **1** = strongest):

| Barrier | Rank **1–5** |
|---|---|
| Costs — **transactions / energy** | _____ |
| Standards / interoperability | _____ |
| Legal / contractual uncertainty | _____ |
| Unclear ROI vs cloud databases | _____ |
| Specialist skills gap | _____ |

**Q‑D6.** Free

---

[shared knowledge: trustrouter_expert_questionnaire_v5_real_survey_instrument.md] hic** and **procedural** audit evidence | **Qualified electronic signature** dossier + tamper‑evident log |
| **IC** | **Independent Confirmation (IC)** | **Independent** cross‑checks (second party, second sensor set, etc.) | **Second independent audit** of the same quantities |
| **L** | **Legal compliance (L)** | Binding **regulatory** / **statutory** obligation attached to the datum | **Mandatory** building‑code or **energy performance** disclosure class |
| **C** | **Criticality (C)** | **Safety**, **financial**, or **contractual** impact if the datum is wrong | **Life‑safety** structural dependence (e.g. occupied **hospital** roof) |

**Q-B2a / b.** **Most important** · **Least important** *(one each among the six)*:

○ **Quality (Q)** · ○ **Provenance Trust (PT)** · ○ **Verification

Reminder, regardless of any wording used above in the reference material: in your JSON answer, "best", "worst", and every key in "best_to_others"/"others_to_worst" must be exactly one of these bare codes: "Q", "PT", "V", "IC", "L", "C" -- never the full label (e.g. "DVS", not "DVS (Data Value Score)" or "Data Value Score"). Respond with ONLY the JSON object, no other text.
