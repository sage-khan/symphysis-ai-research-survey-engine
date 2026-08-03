# Symphysis: Open Source, Patent, or Something Else? An IP Strategy Analysis

Prepared 2026-08-03. Written for Dan's specific situation, not as generic startup advice.

## The one fact that changes everything else

Before weighing open source against patenting, there is a prior question: **is this
even Dan's IP to dispose of alone?**

Dan is a Marie Sklodowska-Curie Actions (MSCA) fellow under a Horizon Europe grant,
hosted at Universidad de Granada. Under the Horizon Europe Model Grant Agreement
(Article 16.2 and Annex 5), **results produced under the grant are owned by the
beneficiary institution that generates them, by default: UGR, not the individual
researcher.** The fellow is guaranteed royalty-free access rights to use the results
for the project's own research activities, but ownership sits with the host
institution unless national law says otherwise (European Commission IP Helpdesk,
"Ownership in Horizon Europe: who gets what," 2022; MSCA IP management fact sheet).

Symphysis was built, on the record, as tooling supporting the TrustRouter/BSI paper,
which is PhD research under this exact grant. That makes a strong case that Symphysis
falls inside the grant's results, not outside it as a personal side project. This
doesn't mean Dan loses everything. It means the choice isn't "open source vs. patent
vs. tell no one," it's "which of these paths can Dan pursue *without* UGR, and which
require UGR's sign-off first." That reframes "should I involve the university" from a
strategic preference into a legal question with a fairly clear answer: **UGR is
already involved, whether Dan loops them in or not.**

UGR's OTRI (Oficina de Transferencia de Resultados de Investigación) is the office
that actually handles this. UGR runs a mandatory doctoral-programme module on IP and
patentability specifically for 2nd- and 4th-year PhD students, delivered through the
Escuela de Posgrado, which confirms OTRI is the right first call. No public UGR
document specifies exact ownership splits or royalty terms for student-generated
software, so this genuinely needs a direct, specific conversation with OTRI rather
than an inference from general policy.

## A second fact that is urgent, not just important

Dan is actively drafting the TrustRouter/BSI paper, which describes Symphysis's
methodology. **Publishing that paper first can foreclose patenting Symphysis
everywhere except the United States.** The US gives an inventor a 12-month grace
period after their own public disclosure before it counts as prior art against their
own later filing. The European Patent Office, and most of the rest of the world, give
no such grace period: publication before filing destroys novelty outright (Mewburn
Ellis, "Grace periods for disclosure of an invention before applying for a patent";
Nature Communications, "The dilemma of patenting versus publishing," 2023).

Concretely: if Dan wants to preserve the *option* of a European patent, that decision
needs to happen before the paper is submitted, not after. If the paper goes out first,
the European patent door closes on submission day, and only a narrower US-only path
remains open for 12 months. This is worth flagging to OTRI explicitly and soon, even
if the eventual answer is "we're not patenting this," because the option disappears on
its own schedule regardless of when Dan gets around to deciding.

## What the realistic paths actually look like

**Patent it individually.** A US provisional filing runs roughly USD 2,500 all-in; a
full utility patent, even at reduced micro-entity fees, realistically runs USD
5,000 to 15,000+ before a single dollar of licensing revenue exists, and that's before
considering that UGR, not Dan, likely holds the underlying rights to file at all. This
path requires capital Dan has stated he doesn't have, on an asset he may not solely
own, racing a publication deadline. It is not a good fit for this situation.

**Approach Microsoft or a similar company directly, unprotected.** Large companies
routinely refuse to sign NDAs for unsolicited pitches specifically to avoid the legal
exposure of "you stole my idea" claims later; the standard industry advice for this
route is to file a patent *before* pitching, precisely because without one there is
nothing to protect during the conversation. Combined with the ownership and cost
issues above, walking into a Microsoft conversation today with no patent and no clear
personal title to the IP is a weak position, not a strong one. This is realistically
not viable as a first move.

**Stay quiet, tell no one, build in the dark.** This is the riskiest option on the
table, not the safest one. It doesn't resolve the ownership question, it just delays
UGR discovering it, and if Symphysis becomes something valuable while its Horizon
Europe origins are undisclosed, that's a materially worse conversation to have later
than a proactive one now. Anonymity also throws away the one asset Dan can
unambiguously bank right now regardless of who owns the code: his own name and
track record as the person who built it.

**University spinout or licensing, via OTRI.** This is a real and normal path, and
crucially it doesn't require Dan to personally fund a patent. The tradeoff is equity
or royalty share: US universities typically take a single-digit percentage in
spinouts, but European institutions have been documented taking significantly more,
in some reported cases 40%+, with wide variation by institution (Oxford University
Innovation; Global Venturing reporting on university spinout equity norms). Whether
UGR would pursue this for a research tool like Symphysis, and on what terms, is
exactly the question to put to OTRI, not to guess at.

**Open source it.** This is the path with the best evidence behind it for Dan's
specific position: a PhD student with no capital, an imminent publication, and an
existing pattern of open-sourcing his own work (VERITAS-AIDB is already Apache 2.0;
CodeGuardian and the Ascon implementations are public). Published research shows
open-sourced research software is associated with higher citation counts and is
perceived by reviewers as more rigorous, not less (arXiv:2410.04286, HCI open-science
study; the Journal of Open Source Software's own design rationale, arXiv:1707.02264).
No evidence was found that this hurts an academic's later career prospects; if
anything the signal runs the other way. Open-sourcing also functions as a defensive
publication: once the code and its description are public, nobody else can quietly
patent the same mechanism out from under Dan later. It preserves reputation and
adoption value while costing nothing to execute, and it does not foreclose future
monetization models (below) if the project ever grows into something worth
commercializing.

## Monetizing an open-source tool without startup capital

Open source and "no money in this" are not the same statement. The realistic
monetization ladder, roughly in order of how little capital each requires:

1. **Reputation and career capital first.** Citations, adoption, invited talks, and a
   stronger academic CV are real returns even if no money changes hands. Given Dan is
   mid-PhD, this is not a consolation prize, it's the return that actually compounds
   fastest right now.
2. **Consulting and integration work**, using Symphysis as the credibility anchor
   rather than the product itself: this requires no capital and no permission beyond
   what OTRI already allows for a PhD student's outside work.
3. **A hosted or managed version later**, once there's real usage: this is the model
   Ollama and Hugging Face both eventually built on, though it's worth being precise
   that both were multi-founder, VC-funded companies from early on, not solo
   bootstrapped projects; Ollama has raised roughly USD 88M across a Y Combinator
   start and subsequent rounds (TechCrunch, July 2026), and Hugging Face is valued
   near USD 4.5B (Axios, 2023). These are the ceiling of the open-source-to-company
   pipeline, not the median outcome, and neither is a near-term plan for Dan; they are
   evidence that the *path* (open source first, funding later, once traction exists)
   is a proven one, not evidence that any specific project will get there.
4. **A university-brokered licensing or spinout deal**, only if and when the tool
   demonstrates enough real-world traction to be worth OTRI's time to structure, and
   only with UGR's ownership question already settled rather than contested after the
   fact.

## Recommendation

Given no personal capital, an imminent publication, a Horizon Europe funding source
that presumptively assigns ownership to UGR, and an existing personal pattern of
open-sourcing research tools:

1. **Talk to OTRI this week, not after the paper is out.** Not to ask permission to
   open source (that conversation can happen in parallel), but specifically to ask
   whether UGR has any interest in patenting before the TrustRouter/BSI paper is
   submitted, since that window closes on submission day for anything outside the US.
   Getting a clear "no, go ahead and publish" from OTRI is itself a valuable, fast,
   low-cost outcome that removes the ownership cloud entirely.
2. **Plan to open source Symphysis**, consistent with VERITAS-AIDB, once OTRI has
   confirmed there's no patent interest. Apache 2.0 (matching Dan's existing
   convention) is a reasonable default: permissive, adoption-friendly, and compatible
   with every monetization path in the ladder above if the project ever grows into
   one.
3. **Do not pursue an individual patent.** The combination of cost, the ownership
   question, and the publication-timing conflict makes this the weakest option
   available, not a live option to weigh evenly against the others.
4. **Do not approach Microsoft or similar companies as a first move.** There's
   nothing to protect the conversation with yet, and no clear personal title to what
   would be offered. Revisit this only after OTRI's answer, and only if Symphysis
   develops enough independent traction as an open-source project to make a
   partnership conversation about integration or investment, not about "here's my
   idea," which is the version companies are structurally unwilling to engage with
   anyway.
5. **Do not go quiet.** It doesn't protect Dan; it just moves the ownership
   conversation with UGR from now, on his terms, to later, on someone else's.

## Open-source execution: how to actually go about it

This section assumes the decision already reasoned through above: no patent, open source,
Apache 2.0, timed with the TrustRouter/BSI paper. It does not relitigate that decision; it is
the concrete checklist for carrying it out, since "we've decided to open source it" and "it is
actually, correctly open source" are different amounts of work.

### 0. The one prerequisite this document already flagged

Nothing below should happen before OTRI has given a clear answer on patent interest (see
"Recommendation," item 1, above). That is not a formality to skip because the decision already
feels made; it is the one step with a real, one-way deadline (publication destroys novelty
outside the US, with no grace period). Everything else in this checklist can happen in
parallel with, or immediately after, that conversation.

### 1. Repository hygiene, before flipping to public

- **License file.** Add a real `LICENSE` file with the Apache 2.0 text at the repo root, not
  just a mention in the README. GitHub's own license picker generates the correct file; do not
  hand-write it. This repo does not have one yet.
- **`CITATION.cff`.** Research software gets cited differently from a typical open-source
  project: a `CITATION.cff` file at the repo root tells GitHub to render a "Cite this
  repository" button and gives anyone citing Symphysis in a paper the exact author, title, and
  version to use, rather than an ad hoc citation someone else invents. Worth doing before launch
  since the TrustRouter/BSI paper will itself cite this repository.
- **`CONTRIBUTING.md`.** Even a short one (how to run tests, branch/PR expectations, where to
  file issues) signals the project is actually open to outside contribution, not just
  open-viewing. This matters specifically for the Ollama/Hugging Face comparison below: both
  became known for being easy to contribute to, not just easy to read.
- **GitHub repo metadata.** Description, topics (e.g. `llm-agents`, `expert-elicitation`,
  `best-worst-method`, `research-tooling`), and a social preview image are what someone actually
  sees before they click through; right now the repository has none of these set.
- **A tagged `v0.1.0` release**, not just a `main` branch. A release with real release notes
  (this repo's own `changelog.md` already has the material) gives the first external user a
  fixed point to install against instead of "whatever `main` happens to be today."
- **Stop renaming.** This project has already been renamed three times internally (SAGE, then
  a working name, then Symphysis) before ever going public. That churn is invisible to an
  internal collaborator but fatal to an external one: a bookmarked link, a cited GitHub URL, or
  a PyPI package name that changes after launch actively breaks other people's work. Treat
  "Symphysis" as final before the repository goes public, precisely because renaming after
  launch costs real goodwill in a way renaming before launch does not.

### 2. Timing: launch with the paper, not before or long after

The evidence already cited above (arXiv:2410.04286; the JOSS design rationale, arXiv:1707.02264)
is specifically about open-sourced *research* software, which draws its credibility from being
the concrete implementation behind a citable paper, not from standing alone as a generic
product. Concretely:

- Making the repository public and submitting the TrustRouter/BSI paper should happen close
  together, ideally the same week, once OTRI has cleared it. A repository that's been public
  for six months before the paper appears loses the "here is the artifact behind this result"
  framing; a repository that appears only long after the paper loses the citation traffic the
  paper itself would have driven to it while it's freshest.
- The paper's own text should link the repository (see the companion note on adding a
  Symphysis architecture section to the TrustRouter/BSI paper) and the repository's README
  should link back to the paper once it has a DOI or arXiv ID. Each drives traffic to the
  other; neither works alone.

### 3. Personal-brand rollout, using the channels already in place

Dan already has exactly the channels this needs, and has already used them for VERITAS-AIDB:
a Medium blog, a LinkedIn newsletter, a personal LinkedIn profile that already mentions Veritas,
and (as of this session) a GitHub profile README and portfolio site that now list Symphysis as
a project. The rollout does not need new infrastructure, it needs sequencing:

1. **A dedicated Medium post announcing Symphysis on its own terms**, not folded into a Veritas
   update. Symphysis is explicitly general-purpose (any expert-elicitation survey, any domain),
   and burying that framing inside a Veritas-specific post undersells exactly the part that
   makes it interesting to someone who has never heard of TrustRouter or BSI. Model it on the
   existing Veritas technical deep-dive (linked from `project-details.md`): what problem it
   solves, the Agent Card design, a real worked example (the BSI/TrustRouter panel is the
   obvious one, since it's already the fully-implemented, tested use case), and a link to the
   repository.
2. **A LinkedIn post from the personal profile**, timed to the Medium post and the repository
   going public, cross-posted or referenced in the next LinkedIn newsletter issue rather than
   competing with it for the same news. State plainly that Symphysis grew out of the
   TrustRouter/BSI PhD research, and is a general-purpose tool now, not a Veritas sub-component;
   that distinction is the whole reason it's being spun out as its own announcement rather than
   folded into the existing VERITAS-AIDB narrative.
3. **Cross-link, do not merge, the two identities.** VERITAS-AIDB's own project rules already
   describe Symphysis-shaped tooling as "supporting" the TrustRouter/BSI research; keep that
   framing consistent everywhere it's mentioned (CV, portfolio, LinkedIn, the paper itself):
   Symphysis is a tool that came out of this PhD's research, now maintained as its own
   general-purpose open-source project, not a renamed piece of Veritas.

### 4. What "the Ollama or Hugging Face of X" actually requires, and what's already true

That comparison is aspirational and worth being precise about, since it names a destination,
not a starting position. What Ollama and Hugging Face actually had that made the comparison
apt: a genuinely simple local-first experience, thorough documentation, and (per the earlier
analysis) venture funding and multiple founders well before either became a household name in
its niche. Realistically, for Symphysis today:

- **Already true**: a real, working local-first pipeline (Ollama-based agents need no API key
  or cloud account), a documented Agent Card format anyone can inspect and hand-edit, a test
  suite, and (as of this session) both a Swagger/OpenAPI reference and a narrative README.
- **Not yet true, and fine to say so rather than overclaim**: no packaged CLI or PyPI
  distribution yet (tracked in the README's "Future enhancements" section), no external
  contributors, no hosted/managed offering. The monetization ladder already laid out above
  (reputation first, consulting second, a hosted version only once real usage exists) applies
  here too: describe Symphysis today as "built the same way Ollama and Hugging Face started,
  open source and research-driven," not as already at their scale. The first is true and
  credible; the second invites an easy, deserved correction from anyone who checks.

## What this document is not

This is a synthesis of publicly available facts about Horizon Europe IP rules,
university spinout norms, and patent timing, plus a recommendation reasoned from
those facts and from Dan's stated situation. It is not legal advice, and the one
action item that actually matters on a clock (talking to OTRI about patent interest
before publishing) should happen regardless of anything else in this document,
because that specific window closes on its own schedule.

## Sources

- European Commission IP Helpdesk, "Ownership in Horizon Europe: who gets what,"
  2022. https://intellectual-property-helpdesk.ec.europa.eu/news-events/news/ownership-horizon-europe-who-gets-what-2022-04-25_en
- IP Helpdesk, "IP Management in MSCA" fact sheet.
  https://www.horizon-europe.gouv.fr/sites/default/files/2021-07/h2020---ipr-helpdesk---ip-management-in-msca-3950.pdf
- UGR Escuela de Posgrado, doctoral-programme patentability training module.
  https://escuelaposgrado.ugr.es/doctorado/escuelas/actividadesformativas/patentes
- UGR OTRI, Patent Blog. https://otriweb.ugr.es/patent-blog/
- PatentBrief, "Patent cost" overview, 2026. https://patentbrief.org/patent-cost
- Oxford University Innovation, spinout equity FAQ.
  https://innovation.ox.ac.uk/com_technology_faqs/gets-equity-spin/
- Global Venturing, reporting on university spinout equity norms (US, UK, Europe).
  https://globalventuring.com/university/us-and-canada/us-university-spinouts-investing/
- TechCrunch, "Popular open-source AI developer tool Ollama raises $65M," July 2026.
  https://techcrunch.com/2026/07/09/popular-open-source-ai-developer-tool-ollama-raises-65m-grows-to-nearly-9m-users/
- Axios, on Hugging Face's Series D valuation, 2023.
  https://axios.com/2023/08/24/hugging-face-ai-salesforce-billion
- spectup, "How to protect your idea when pitching it."
  https://www.spectup.com/resource-hub/how-to-protect-your-idea-when-pitching-it
- Mewburn Ellis, "Grace periods for disclosure of an invention before applying for a
  patent." https://www.mewburn.com/law-practice-library/grace-periods-for-disclosure-of-an-invention-before-applying-for-a-patent
- Nature Communications, "The dilemma of patenting versus publishing," 2023.
  https://www.nature.com/articles/s41467-023-37243-z
- arXiv:2410.04286, open-science practices study in HCI research.
- arXiv:1707.02264, Journal of Open Source Software design rationale.
