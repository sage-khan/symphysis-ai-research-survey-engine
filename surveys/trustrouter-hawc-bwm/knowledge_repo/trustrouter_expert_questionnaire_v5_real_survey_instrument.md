# Blockchain Suitability Index (BSI): Expert questionnaire

**Version 5 · May 2026**

Universidad de Granada · University of Ljubljana

---

## Practical information

Completing every section **carefully** typically requires **45–70 minutes** for most experts; some respondents need **up to 90 minutes**. You may pause and return if the study team provides a resumable link.

---

## Informed consent

This study examines how specialists prioritise storage options for digital construction and deep-renovation data. Participation is voluntary; withdrawal is always allowed. Responses are analysed **without** your name unless you choose to identify yourself later for scheduling. Outputs appear only in aggregated or anonymised form. Data reside on institutional systems and are retained as required under applicable data-protection norms (normally up to seven years).

**Approval reference:** *[insert institutional ethics-committee approval number]*

**Study contacts:** *[insert email addresses]*

- [ ] I have read this information and freely agree to contribute.

---

## Background

Renewal-centric projects accumulate heterogeneous records (reports, **Building Information Modelling (BIM)**, inspections, metering, certifications). Subsequent actors must often rely on **integrity** — regulators, insurers, owners, and juridical oversight. Ordinary databases silently permit rewriting; **decentralised ledgers** improve **tamper‑evidence** (changes become detectable), but they are costly and limited in throughput and payload. Routing must therefore discriminate **in a rational, transparent and automatic way**, using **quantitative indicators** as main building blocks.

**Blockchain Suitability Index (BSI)** denotes a composite score computed **after** explicit **gates** covering legal / privacy suitability, contractual confidentiality limits, and minimum technical practicality. Your task is to quantify **priorities**, not to configure a particular vendor product.

### How the score is built *(orientation only)*

The technical manuscript aggregates four multiplicative pillars. Experts reason more reliably when **all criteria are framed so that “higher / more” is better**. **Technical friction** is therefore surveyed as **Technical feasibility fit (F)**:

- **F = 1** → excellent fit for a plausible **permissioned‑ledger** posture (realistic size, update rate, latency, cost).
- **F = 0** → very poor fit (heavy bulk, churn, latency, or cost burdens).

Implementation maps **Technical feasibility fit (F)** ↔ **Performance penalty (P)** through **P = 1 − F**:

```
BSI = DVS × (1 − P) × (1 + E) × A     with P ≡ 1 − F
```

Where **DVS** = **Data Value Score (DVS)**, **E** = **Economic Value (E)**, **A** = **Attack Resistance (A)**. Because **(1 + E)** lies in **[1, 2]**, **BSI can reach up to 2.0** when all inputs are high. **Thresholds in Part 5 use this [0, 2] scale.**

### Canonical glossary *(use these exact wordings in Part 3 comparisons)*

| Short | Full label | Meaning |
|---|---|---|
| **DVS** | **Data Value Score (DVS)** | Composite trust from **Quality (Q)**, **Provenance Trust (PT)**, **Verification Strength (V)**, **Independent Confirmation (IC)**, regulatory / legal weight (**Legal compliance (L)**), and consequence if wrong (**Criticality (C)**). |
| **F** | **Technical feasibility fit (blockchain)** | How well the artefact fits realistic ledger limits (**size**, **update rate**, **latency**, **cost**). **Higher F = better fit.** |
| **E** | **Economic Value (E)** | Downstream **financial** or **asset** value at risk if the datum is lost or corrupted. **Higher E = greater value.** |
| **A** | **Attack Resistance (A)** | Difficulty of **undetected tampering** (**identity fraud**, **device compromise**, **insider abuse**). **Higher A = stronger resistance.** |

### Storage tiers *(used in scenarios and Part 4)*

You do **not** need to be a blockchain specialist. Roughly:

| Short | Full name | Plain description |
|---|---|---|
| **BLOCKCHAIN** | Full on-chain tier | The **record** (or its essential payload) lives **on the distributed ledger** itself: **strong tamper‑evidence**, **higher cost** and **stricter size / speed limits**. |
| **IPFS_HASH** | Hybrid (**InterPlanetary File System (IPFS)** + cryptographic **hash**) tier | The **large file** rests on a **content‑addressed file network** (the IPFS idea); **only a short cryptographic hash** (digital fingerprint of the file) plus metadata is **posted on the ledger**, so tampering shows up later without uploading the entire file **on‑chain**. |
| **OFFCHAIN** | Off-chain / conventional tier | **Traditional database** or file store: **flexible and cheap**, **weaker decentralised integrity guarantees** unless added by other means. |

*(Wording aligned with the institutional survey pilot: “which pieces of construction data deserve the cost of blockchain storage” — trust vs cost trade-off.)*

---

### Part 1 — Reference scenario (≈2 min)

**Hospital Real** (Granada, Spain) **deep renovation**: a multi-decade **public** asset with mixed **structural**, **energy**, and **compliance** documentation. Data must serve **institutional owners**, **insurers**, and **authorities** for decades. This setting is a **shared reference only**; answers should reflect **general professional judgement**, not only this building.

---

### Part 2 — Profile (≈5 min)

**Q-A1.** Primary role *(one choice)*

- Structural / civil engineer  
- **BIM** (**Building Information Modelling (BIM)**) coordinator / manager  
- Construction project manager  
- Architect / **MEP** (**Mechanical, Electrical, and Plumbing (MEP)**) engineer  
- Facility manager / compliance officer  
- **Blockchain** / **DLT** (**Distributed Ledger Technology (DLT)**) specialist  
- Researcher / lecturer (construction, BIM, **ICT** (**Information and Communication Technology (ICT)**), blockchain, analytics)  
- Doctoral or Master’s student — related topic  
- Other: ____________________

**Q-A2.** Years of relevant experience: **< 2 · 2–5 · 5–10 · > 10**

**Q-A3.** Highest completed education: Bachelor’s · Master’s · Doctorate (PhD) and/or professional licence (**PE**, Professional Engineer, **CEng**, Chartered Engineer, or equivalent): __________

**Q-A4.** Primary country or region of practice: ____________________

**Q-A5.** Familiarity **1–5** (1 = none, 5 = expert). One mark per row.

| Topic | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| **BIM / IFC** (**Building Information Modelling (BIM) / Industry Foundation Classes (IFC)**) | ○ | ○ | ○ | ○ | ○ |
| **Blockchain / DLT** (**Distributed Ledger Technology (DLT)**; includes “blockchain”) | ○ | ○ | ○ | ○ | ○ |
| **Digital building logbooks** | ○ | ○ | ○ | ○ | ○ |
| Data quality norms (**ISO 25012** international data-quality model, “**ISO 25012 type**”) | ○ | ○ | ○ | ○ | ○ |
| Construction codes / conformity assessment | ○ | ○ | ○ | ○ | ○ |
| **EU** privacy / **GDPR** (**General Data Protection Regulation (GDPR)**) + digital acts | ○ | ○ | ○ | ○ | ○ |
| Lineage / provenance | ○ | ○ | ○ | ○ | ○ |

**Attention check 1:** On the **Blockchain / Distributed Ledger Technology (DLT)** row only, please select **3**.

**Q-A6.** Have you observed disputes about construction-data integrity? **Frequently · Occasionally · Not that I recall**

---

### Part 3 — Best–Worst comparisons (≈25–35 min)

Abbreviations used in the method literature: **Best‑to‑Others (BTO)** means “compare **your Best criterion** to **each** other criterion”; **Others‑to‑Worst (OTW)** means “compare **each** criterion **to your Worst**.” *(Occasionally abbreviated **BOT** — same meaning.)*

#### What you do in every block (3.1 → 3.7)

1. Choose **Best** (most influential for **routing** construction data to **full on-chain**, **hybrid**, or **conventional** storage).  
2. Choose **Worst** (least influential).  
3. **Best‑to‑Others (BTO)** — using **1 = equal importance** through **9 = extremely more important**, for **each** criterion **j**: how much **more important** is **your Best** **than j**? When **j** **is** your Best, enter **1**.  
4. **Others‑to‑Worst (OTW)** — same scale: for **each j**, how much **more important** is **j than your Worst**? When **j** **is** your Worst, enter **1.**

**Midpoints** on the scale are **2, 4, 6, 8.**

**Online forms:** row order inside each matrix may **rotate**; labels stay the same. **Paper:** order is fixed as printed.

---

#### Worked miniature example *(do **not** copy numbers into your questionnaire)*

Suppose the factors are **Camera · Battery · Price**; **Best = Battery**, **Worst = Camera**.

**BTO** — row = “**Battery** compared to each column”:

| BTO: **Best = Battery** versus → | Camera | Battery | Price |
|---|---|---|---|
| Rating **1–9** | 7 | 1 | 3 |

*(Battery vs Battery = **1**. Battery is judged **much** more important than Camera (**7**) and **moderately** more than Price (**3**).)*

**OTW** — row = “each column **compared to Worst = Camera**”:

| OTW: each versus **Worst = Camera** → | Camera | Battery | Price |
|---|---|---|---|
| Rating **1–9** | 1 | 7 | 4 |

*(Camera vs Camera = **1**; Battery is far above Camera (**7**); Price is moderately above Camera (**4**).)*

Pairwise entries feed a **Bayesian Best–Worst** model (Mohammadi & Rezaei 2020) and **consistency** checks (Rezaei 2015).

---

#### **Reminder before each matrix** *(read once, then apply to every table below)*

- **BTO row:** “**My Best is \_\_\_\_\_\_.** How much **more important** is **my Best** **than** **[column header]**?” → write **1–9** under each column (self‑pair = **1**).  
- **OTW row:** “**My Worst is \_\_\_\_\_\_.** How much **more important** is **[column header]** **than** **my Worst**?” → write **1–9** (self‑pair = **1**).

---

### Glossary lock — Part 3.1 quartet

Use **exactly** these four **full** labels in **Best / Worst** and in **every** comparison row:

1. **Data Value Score (DVS)**  
2. **Technical feasibility fit (blockchain)**  
3. **Economic Value (E)**  
4. **Attack Resistance (A)**

#### 3.1 — Top-level quartet

**Q-B1a.** Which factor is **most influential** for deciding whether construction data belongs on a **ledger**?

○ **Data Value Score (DVS)** · ○ **Technical feasibility fit (blockchain)** · ○ **Economic Value (E)** · ○ **Attack Resistance (A)**

**Q-B1b.** Which is **least influential**?

○ **Data Value Score (DVS)** · ○ **Technical feasibility fit (blockchain)** · ○ **Economic Value (E)** · ○ **Attack Resistance (A)**

**Q-B1c. Best‑to‑Others (BTO).** My **Best** is: __________________ (name one of the four above). Rate **1–9** how much **more important** **your Best** is **than** each row label. **Self‑pair = 1.**

| **Best** versus → | Rating **1–9** |
|---|---|
| **Data Value Score (DVS)** | _____ |
| **Technical feasibility fit (blockchain)** | _____ |
| **Economic Value (E)** | _____ |
| **Attack Resistance (A)** | _____ |

**Q-B1d. Others‑to‑Worst (OTW).** My **Worst** is: __________________. Rate **1–9** how much **more important** each row is **than your Worst**. **Self‑pair = 1.**

| Criterion versus **Worst** → | Rating **1–9** |
|---|---|
| **Data Value Score (DVS)** | _____ |
| **Technical feasibility fit (blockchain)** | _____ |
| **Economic Value (E)** | _____ |
| **Attack Resistance (A)** | _____ |

---

#### 3.2 — Six constituents inside **Data Value Score (DVS)**

These sit **inside** the **Data Value Score (DVS)** pillar (not separate top-level factors).

| Short | Full name | Definition | Example |
|---|---|---|---|
| **Q** | **Quality (Q)** | **Intrinsic** and **contextual** fidelity of the record | **Industry Foundation Classes (IFC)**‑valid coordination model |
| **PT** | **Provenance Trust (PT)** | Trust in **who** created the data and **custody** until handover | Signed report from a **chartered structural engineer** |
| **V** | **Verification Strength (V)** | Strength of **cryptographic** and **procedural** audit evidence | **Qualified electronic signature** dossier + tamper‑evident log |
| **IC** | **Independent Confirmation (IC)** | **Independent** cross‑checks (second party, second sensor set, etc.) | **Second independent audit** of the same quantities |
| **L** | **Legal compliance (L)** | Binding **regulatory** / **statutory** obligation attached to the datum | **Mandatory** building‑code or **energy performance** disclosure class |
| **C** | **Criticality (C)** | **Safety**, **financial**, or **contractual** impact if the datum is wrong | **Life‑safety** structural dependence (e.g. occupied **hospital** roof) |

**Q-B2a / b.** **Most important** · **Least important** *(one each among the six)*:

○ **Quality (Q)** · ○ **Provenance Trust (PT)** · ○ **Verification Strength (V)** · ○ **Independent Confirmation (IC)** · ○ **Legal compliance (L)** · ○ **Criticality (C)**

**Q-B2c. Best‑to‑Others (BTO).** **Best** = __________________ (abbreviation **Q / PT / V / IC / L / C** allowed here only after first mention above).

**BTO:** *How much **more important** is **your Best** than each column header? **Best versus Best = 1.***

| **Best** versus → | **Quality (Q)** | **Provenance Trust (PT)** | **Verification Strength (V)** | **Independent Confirmation (IC)** | **Legal compliance (L)** | **Criticality (C)** |
|---|---|---|---|---|---|---|
| Rating **1–9** | __ | __ | __ | __ | __ | __ |

**Q-B2d. Others‑to‑Worst (OTW).** **Worst** = __________________.

**OTW:** *How much **more important** is each column **than your Worst**? **Worst versus Worst = 1.***

| … versus **Worst** | **Quality (Q)** | **Provenance Trust (PT)** | **Verification Strength (V)** | **Independent Confirmation (IC)** | **Legal compliance (L)** | **Criticality (C)** |
|---|---|---|---|---|---|---|
| Rating **1–9** | __ | __ | __ | __ | __ | __ |

---

#### 3.3 — Quality triple (**ISO 25012** clusters)

Short labels are standard in our model; meanings:

- **Intrinsic Quality cluster (IQ)** — **accuracy**, **validity**, **uniqueness** (“are the values right in themselves?”)  
- **Contextual Quality cluster (CQ)** — **completeness**, **timeliness** (“right scope and time?”)  
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

| **Best** versus → | **A_sybil** | **A_oracle** | **A_insider** |
|---|---|---|---|
| Rating **1–9** | __ | __ | __ |

| … versus **Worst** | **A_sybil** | **A_oracle** | **A_insider** |
|---|---|---|---|
| Rating **1–9** | __ | __ | __ |

---

#### 3.7 — **Economic Value (E)** sub‑dimensions

| Short | Meaning |
|---|---|
| **E_market** | **Present marketplace demand** |
| **E_liquidity** | **Ease of tokenisation / tradability** (if applicable) |
| **E_demand** | **Projected future demand** (lifecycle, regulation, analytics) |

**Best** __________ **`Worst`** __________

| **Best** versus → | **E_market** | **E_liquidity** | **E_demand** |
|---|---|---|---|
| Rating **1–9** | __ | __ | __ |

| … versus **Worst** | **E_market** | **E_liquidity** | **E_demand** |
|---|---|---|---|
| Rating **1–9** | __ | __ | __ |

---

### Part 4 — Applied judgement (≈12 min)

#### Scenario A — Structural capacity dossier

**Facts:** **Chartered structural engineer** (**≥ 15 years** practice), **digitally sealed** **Portable Document Format (PDF)** structural report (**~2 MB**), **direct institutional upload**, **masonry** load assessment, **no** named occupants or remuneration data; long retention horizon for **insurers** and **authorities**.

| Gate | **Pass** □ | **Borderline** □ | **Fail** □ | Notes |
|---|---|---|---|---|
| **Legal** and **privacy** suitability for **immutable** archiving | | | | |
| **Confidentiality** / **competitive sensitivity** | | | | |
| **Technical practicality** versus realistic **permissioned‑ledger** limits | | | | |

If **no gate is marked Fail** (**Borderline** still allows continuation), score **each** field independently **[0.00 , 1.00]** (**do not** force the nine numbers to **sum** to **1**).

| Field | Score **0–1** | Guidance |
|---|---|---|
| **Quality (Q)** | _____ | Structural–technical fidelity of the dossier |
| **Provenance Trust (PT)** | _____ | Authority + custody story |
| **Verification Strength (V)** | _____ | Signatures / logs |
| **Independent Confirmation (IC)** | _____ | Independent corroboration depth |
| **Legal compliance (L)** | _____ | Regulatory / obligatory weight |
| **Criticality (C)** | _____ | Impact if erroneous |
| **Technical feasibility fit (F)** | _____ | Higher **F** = **better ledger fit** |
| **Attack Resistance (A)** | _____ | Higher **A** = **harder to tamper undetected** |
| **Economic Value (E)** | _____ | Higher **E** = **greater downstream value** |

Recommended tier *(see definitions at start of document)*:  
○ **BLOCKCHAIN** (**full on-chain**) ○ **IPFS_HASH** (**hybrid**) ○ **OFFCHAIN** (**conventional off-chain**)

**Rationale *(optional)*** — you may cite **gates** if relevant and **two or three** of the following angles: **trust / legal weight**; **file size vs ledger limits**; **update frequency**; **who could tamper**; **downstream cost if the record fails**.

_______________________________________________________________________________

#### Contrast vignette (**same renovation project**)

The same renovation also deploys **twenty Internet‑of‑Things (IoT) accelerometers** on a continuous **vibration stream** (**100 ms control** latency target) **and** produces a **daily** **aggregate** dossier (**~10 kilobytes (kB)**: min/max, anomalies, **Secure Hash Algorithm 256‑bit (SHA‑256)** cryptographic commitment binding the raw stream). The **raw stream** fails the **technical feasibility** gate for **ledger anchoring at source rate** (**blockchain consensus** is slower than milliseconds).

For the **daily aggregate only**, which tier?  
○ **BLOCKCHAIN** (**full on-chain**) ○ **IPFS_HASH** (**hybrid**) ○ **OFFCHAIN** (**conventional off-chain**)

**Brief note — how reasoning differs from Scenario A *(optional)*.**  
Your note can touch **latency**, **payload rate**, **evidence aggregation**, **oracle / device‑tampering exposure**, **regulatory artefact versus operational telemetry**:

*Example only (your own wording is fine)—“Unlike the static PDF dossier in Scenario A, the raw vibration stream feeds **near‑real‑time structural safety**, so ledger anchoring applies to the **digest**, not each sample. The digest stays **small (~10 kB)** yet carries a **cryptographic anchor** to underlying data; hybrid often balances **cost**, while institutional **signatures** matter less than **sensor provenance**, **oracle risk**, and **throughput realism** compared with Scenario A.”*

Your answer:

_______________________________________________________________________________

#### Task **4C** — Routing six **archetypes**

For each row, circle **exactly one** tier:  
**B** = **BLOCKCHAIN** (**full on-chain**) · **H** = **IPFS_HASH** (**hybrid**) · **O** = **OFFCHAIN** (**conventional off-chain**).

| ID | Sketch | **B** | **H** | **O** |
|---|---|---|---|---|
| **A** | **IFC** parameter subset ~**260 kB**; cyclic design review | ○ | ○ | ○ |
| **B** | **HVAC** (**Heating, Ventilation, Air Conditioning (HVAC)**) statutory inspection certificate ~**50 kB** | ○ | ○ | ○ |
| **C** | Construction drawings + technical specifications ~**20 MB** (**megabytes**) | ○ | ○ | ○ |
| **D** | Material / laboratory test certificates ~**500 kB** | ○ | ○ | ○ |
| **E** | Daily construction progress photographs ~**5 MB/day** | ○ | ○ | ○ |
| **F** | Meeting minutes + **Requests for Information (RFIs)** logs ~**100 kB** | ○ | ○ | ○ |

**4C-i.** Item where choice was **firmest** *(optional one sentence)*:

_______________________________________________________________________________

**4C-ii.** Item where choice was **hardest**. Name **two** dimensions that pulled opposite ways (e.g. **Technical feasibility fit (F)** vs **Economic Value (E)**):

_______________________________________________________________________________

---

### Part 5 — Thresholds and reflection *(≈5 min; **optional**)*

Recall: **Blockchain Suitability Index (BSI) = Data Value Score (DVS) × (1 − Performance penalty (P)) × (1 + Economic Value (E)) × Attack Resistance (A)** with **Performance penalty (P) = 1 − Technical feasibility fit (F)**. With inputs in **[0, 1]** (and **(1 + Economic Value)** in **[1, 2]**), composites usually fall in **[0 , 2]**; numeric answers below assume that **interval [0.00 , 2.00]**.

Interpretation anchors for non‑specialists:

- **“Higher BSI slice”** → data where **combined trust**, **technical fit**, **economic stake**, and **tamper hardness** jointly justify **stronger anchored storage.**  
- **“Lower BSI slice”** → routing toward **lighter** tiers (**OFFCHAIN**) or intermediate **Integrity hash on ledger, bulk file elsewhere** (**IPFS_HASH**) per definitions above.

---

**Q‑D1.** Threshold **≥ 1.20** for **recommended full on-chain (BLOCKCHAIN) routing** — does this feel appropriate?

○ **About right** · ○ **Too low** (should require **even higher** composite) · ○ **Too high** (would allow lower composite)

Suggested alternative (**[0.00 , 2.00]**): ________ **Brief rationale:**

_______________________________________________________________________________

**Q‑D2.** Lower bound **0.80** for the **hybrid (IPFS + hash anchor)** band — comfortable?

○ **About right** · ○ **Raise boundary** · ○ **Lower boundary**

Suggested alternative: ________ **Brief rationale:**

_______________________________________________________________________________

**Q‑D3.** Personally — “**Prefer anchored ledger posture** when BSI ≥ ________”; “**Avoid primary ledger posture** when BSI < ________”; **ambiguous band** commentary:

_______________________________________________________________________________

_______________________________________________________________________________

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

**Q‑D6.** Free remarks *(optional)*:

_______________________________________________________________________________

**Attention check 2.** Value instructed for **Blockchain / DLT**: ○ 1 ○ 2 ○ 3 ○ 4 ○ 5

---

### Optional follow-up (**anonymous Delphi‑style briefing**)

If **aggregated** weight summaries circulate later (~**15 min** voluntary revisit):  
○ Interested · ○ Depends on schedule · ○ No  **Email *(optional)*:** ____________________

---

### Appendix *(method — optional deeper reading)*

**Bayesian Best–Worst Method (Bayesian BWM):** pooled weights follow Mohammadi & Rezaei (2020); individual posteriors summarise uncertainty.

**Consistency Ratio (CR):** Rezaei (2015); **investigator flagging** thresholds apply as per protocol (**CR > 0.10** per block, etc.).  
**Survey software note:** Implementations (**e.g. LimeSurvey**) should **randomise row order inside each BTO/OTW rating table** independently per respondent; **paper instruments** omit rotation.

---

### References

Mohammadi & Rezaei (2020) **Omega** 96, 102075.  
Rezaei (2015; 2016) **Omega** 53 & 64.  
**ISO/IEC 25012:2008** — software / data‑quality vocabulary.
