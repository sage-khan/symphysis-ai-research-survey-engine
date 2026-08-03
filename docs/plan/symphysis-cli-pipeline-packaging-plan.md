# Symphysis: CLI, Config Schema, Four-Layer Pipeline, and PyPI Packaging Plan

Planning document only, per your instruction ("PLAN THIS in depth ... i will read the plan
then we start working on it"). Nothing in this document has been implemented. It maps your new
CLI concept and four-layer pipeline sketch onto the code that already exists in
`symphysis-ai-research-survey-engine`, flags where your sketch and the current architecture
diverge, and lays out an implementation order with tests and PyPI publishing at the end.

Where a design choice was genuinely yours to make (naming, ordering, scope for v1), I picked
the option I'd recommend and said why, rather than leaving it open, since you asked for a plan
to read and react to, not a menu.

---

## 0. What already exists (the real starting point, not a rewrite)

Verified by reading the actual code, not assumed:

- **CLI**: `src/agentic_survey/cli.py` (50 lines). One subcommand, `run <survey_dir>`, built
  with the stdlib `argparse`. The docstring mentions a `new` subcommand but it is not
  implemented yet.
- **Survey config**: `src/agentic_survey/config.py`'s `SurveyConfig` — reads `survey.yaml`
  (id, title, instrument, instrument_params, weighting) plus `agents/*.json` (one Agent Card
  per agent). This is the survey-level config; there is no project-level or global config file
  yet beyond `config/defaults.yaml` (provider base URLs, model/sampling/RAG defaults, denylist)
  read through `app_config.py`.
- **Agent Card**: `src/agentic_survey/agent_card.py` — one portable JSON per agent: DID (via
  `did_key.py`), `ModelSpec` (provider, model name, temperature, max_tokens, top_p, seed),
  role description, RAG corpus settings, permissions, guardrails. This already is the
  "Statistician Agent [DID, Agent Card, CV, Personality, Tools, Knowledge]" concept from your
  pipeline sketch, just without a "CV" or "Personality" field named as such yet (see §3).
- **Orchestrator (existing meaning)**: today "orchestrator" in this codebase means the
  natural-language survey-drafting assistant (`web/backend/routers/proposer.py`, task #15) that
  turns a prompt into a draft `survey.yaml` + agent roster for human approval. It does **not**
  run the survey itself; `orchestrator.py`'s `run_survey()` does that, as a plain function, with
  no agent identity of its own. Your new request for an "orchestrator agent" with its own Agent
  Card is a different, new concept that needs a new name to avoid colliding with the existing
  one (see §3.4).
- **Reporting**: `src/agentic_survey/reporting.py` renders **Markdown + PNG charts** only.
  No DOCX, PDF, HTML, Qualtrics, SPSS, or CSV export exists today.
- **Web UI**: FastAPI backend (`web/backend/routers/`: agents, surveys, knowledge_bases,
  knowledge, library, proposer, settings) + React frontend (`AgentLibraryPage`, `SettingsPage`,
  `SurveyDetailPage`, `SurveysPage`). No page yet for configuring a project-level or
  orchestrator-level Agent Card.
- **Packaging**: no `pyproject.toml` yet. `docs/packaging-plan.md` (already written, see
  Appendix A) covers Steps 1-3 of turning `agentic_survey` into an installable package with a
  `symphysis` console-script entry point, published via PyPI's trusted-publisher OIDC flow. This
  document supersedes that one's CLI-subcommand list (§2) with your actual flag grammar, but
  keeps its packaging mechanics (Step 1/Step 3) as the plan to follow.
- **Reference implementation for packaging**: `~/ProgramFiles/text2officeprocessor` is a real,
  working example of everything Step 3 needs:
  - `pyproject.toml`: PEP 621 `[project]` table, `[project.optional-dependencies]` extras
    (`openai`, `claude`, `groq`, `all-llm`, `web`, `dev`), `[project.scripts]` entry
    (`text2officeprocessor = "src.cli.main:main"`), `[tool.setuptools.packages.find]`,
    `[tool.setuptools.package-data]` for bundled non-Python files (templates), `[tool.ruff]`.
  - CLI built with **Typer**, not argparse (`src/cli/main.py`, 946 lines) — subcommands
    `convert`, `analyze`, `batch`, `drawio-export`, `serve`; a `_bundled_templates_dir()` helper
    that resolves bundled assets via `importlib.resources` for installed packages, falling back
    to a relative path for editable/dev installs.
  - `.github/workflows/python-publish.yml`: two jobs, `release-build` (checkout, setup-python,
    `python -m build`, upload artifact) then `pypi-publish` (download artifact, `environment:
    name: pypi` + `id-token: write` + `pypa/gh-action-pypi-publish@release/v1` — the trusted-
    publisher OIDC flow, no stored PyPI token secret). Triggered on `release: types: [published]`,
    not on every push to main.
  - `MANIFEST.in` for sdist completeness alongside `package-data`.

This is the concrete template to copy for Symphysis's own packaging (§6), adapted for Typer
over argparse (see §2.1 for why) and for `agentic_survey`'s actual dependency set (PyMC/numpy for
Bayesian BWM, PyYAML, requests, the RAG stack).

---

## 1. Reconciling your two requests: are they the same thing?

You described two things in the same message:

1. A CLI: `symphysis --project-name <name> --prompt <prompt> --conceptdoc <path> --config
   <path> --surveyfile <path> --output <path> --fix-survey`
2. A four-layer pipeline: Researcher -> Orchestration -> AI Panel -> Collaboration.

These are the same system described at two different altitudes, not two separate things to
build. The CLI is the **entry point into the Researcher Layer** specifically: every one of its
flags (`--prompt`, `--conceptdoc`, `--surveyfile`, `--fix-survey`) maps onto a Researcher-Layer
step (Prompt -> Requirements -> Survey -> Knowledge Base -> Research Goal). Once the Researcher
Layer produces a validated `survey.yaml` + `agents/*.json` + `knowledge_repo/`, everything from
Orchestration Layer onward is what `run_survey()` already does today, extended per §4. §2 and §4
are therefore one plan, read together, not two competing designs.

---

## 2. CLI design

### 2.1 Framework: switch from argparse to Typer

Recommendation: **adopt Typer**, matching `text2officeprocessor`'s proven pattern, rather than
extending the current 50-line argparse script. Reasons: Typer gives you subcommands with typed
options, automatic `--help` generation, and shell completion for free, and it is already the
open-source library this project's sibling package depends on and publishes cleanly — no new
unfamiliar tooling. Add `typer>=0.12.3` to `pyproject.toml`'s core dependencies (§6). This is a
rewrite of `cli.py`'s 50 lines, not a breaking change to any survey-directory format.

### 2.2 Subcommand, not top-level flag soup

Your sketch (`symphysis --project-name <name> --prompt <prompt> ...`) puts every flag at the top
level of the `symphysis` command with no subcommand. Recommendation: **introduce a `new`
subcommand that owns this exact flag set**, i.e. `symphysis new --project-name <name> --prompt
<prompt> --conceptdoc <path> --config <path> --surveyfile <path> --output <path> --fix-survey`,
and keep `run`, `report`, `add-agent` as their own subcommands (per `docs/packaging-plan.md`
Step 2). Reason: a single flat command that does either "create a new survey project" or "fix an
existing survey file" or "run a survey" depending on which optional flags are present is
ambiguous to read and to `--help`; Typer subcommands make each mode's required/optional flags
explicit and self-documenting, exactly like `text2officeprocessor`'s `convert` / `analyze` /
`batch` / `serve` split.

### 2.3 Resolved flag grammar

Your message left three things genuinely ambiguous ("Make sure ddeploy.yaml..." aside, the CLI
grammar itself has real gaps I should flag rather than silently resolve):

- You wrote `--surveyfile (if not given, create this -- output --fix-survey (if added, means
  that the given survety file needs to be checked and improved)`. Read literally this could mean
  either (a) `--surveyfile` is optional and its absence triggers creation, with `--output`
  and `--fix-survey` as separate flags, or (b) `--fix-survey` takes `--surveyfile` as an argument.
  Resolution I recommend: `--fix-survey` is a **boolean flag**, not a flag with its own path
  argument. When passed, it changes the *meaning* of `--surveyfile <path>` from "template to
  extend" to "existing file to validate and repair" — same flag, different downstream branch,
  which matches your parenthetical "(if added, means that the given survety file needs to be
  checked and improved)" describing `--fix-survey` as a mode switch on an already-given
  `--surveyfile`.
- `--conceptdoc` had no space before it in your message (`--conceptdoc<conceptdoc>`); I'm
  treating this as a typo, not a deliberate no-space flag syntax, since Typer/argparse both
  expect `--flag value` or `--flag=value`.
- `--output` was listed with no `<placeholder>` at all in your message; I'm resolving it as
  `--output <dir>`, the survey project directory to write into (defaulting to
  `./<project-name>/` if omitted), distinct from `--surveyfile` which names one specific YAML
  file inside or outside that directory.

Resolved command:

```
symphysis new
  --project-name <name>          # required
  --prompt "<research question>" # one of --prompt / --conceptdoc required
  --conceptdoc <path>            # a concept-sheet doc (md/docx/pdf) to seed requirements from
  --config <path>                # project config (see §3); defaults to ./symphysis.config.yaml
  --surveyfile <path>            # optional: an existing survey.yaml to extend or fix
  --output <dir>                 # where to write the survey project; default ./<project-name>/
  --fix-survey                   # boolean: validate + repair --surveyfile instead of extending it

symphysis run <survey-dir>                       # already exists, unchanged
symphysis add-agent <survey-dir> [--from-library <agent-id> | --interactive]
symphysis report <survey-dir> [--format md|docx|pdf|html|csv|qualtrics|spss]   # see §5
symphysis fix-survey <survey-dir>                # alias for `new --fix-survey`, for discoverability
```

`fix-survey` as both a flag on `new` and its own subcommand is deliberate, not redundant: a user
who already knows they want to repair a file reaches for a verb-named subcommand
(`symphysis fix-survey ./my-survey/survey.yaml`) faster than they'd reach for `new --fix-survey`;
Typer lets one function serve both without duplicating logic.

### 2.4 What `--fix-survey` actually checks

"Checked and improved" needs a concrete definition before it's buildable. Recommendation: reuse
the **QA pre-check** machinery already built for agents (`qa_checks.py`, tasks #28/#29) at the
survey level: schema validation against `SurveyConfig`'s required fields, instrument-params
completeness (every level in a hierarchical BWM tree has `dimensions` + either no `parent_level`
or a `parent_level`/`parent_criterion` pair that resolves to a real level+code, per
`hierarchical_bwm.py`'s own docstring contract), and orphan detection (an agent card referencing
a knowledge base or RAG corpus path that no longer exists). Output: a structured list of
errors/warnings, same shape QA post-check already produces, printed to the terminal and written
to `<survey-dir>/fix-report.md`.

---

## 3. Config file schema

### 3.1 Scope: this is a new file, not a replacement for `survey.yaml`

`survey.yaml` (per-survey: instrument, dimensions, weighting) and `config/defaults.yaml`
(installation-wide: provider URLs, sampling defaults) both already exist and keep their current
jobs. The new `--config <path>` file is a **third, project-level** file sitting between them:
things that describe one research *project* (which may run several surveys over its lifetime)
rather than one survey run or one installation.

### 3.2 Proposed schema (`symphysis.config.yaml`)

```yaml
project:
  name: "<project-name>"
  data_folder: "./data"          # RAG corpora, uploaded concept docs
  project_folder: "./project"    # generated survey.yaml, agents/, reports/ live here

providers:
  default: "ollama"              # or "anthropic", "openai", "manual"
  api_keys:
    anthropic: "${ANTHROPIC_API_KEY}"   # env-var reference, never a literal secret in this file
    openai: "${OPENAI_API_KEY}"
  local_llm:
    base_url: "http://localhost:11434"
    default_model: "qwen2.5:14b"

expert_agents:
  source: "library"               # "library" (pull from Agent Library) | "inline" | "generate"
  library_ids: ["statistician-v1", "hci-professor-v1", "ux-researcher-v1"]
  # OR, if source: inline, full Agent Card fields per agent (rare; library is the common path)

orchestrator_agent:
  agent_card: "./project/orchestrator.agent.json"   # see §3.4
  model:
    provider: "anthropic"
    name: "claude-opus-5"
  responsibilities: ["survey_generation", "task_planning", "panel_selection", "context_management", "knowledge_distribution"]
```

Two rules carried over from existing code and enforced here, not new inventions: (1) **no
literal API keys in a committed file** — `${ANTHROPIC_API_KEY}`-style env-var references only,
consistent with `gitops.md`'s "no secrets in Git" rule and this repo's existing
`.env.example` pattern; (2) this file is **read through the same `app_config.py` merge
mechanism** (`load_defaults()` + override layer) rather than becoming a fourth independent
config-loading code path, so Settings-UI-driven overrides keep working uniformly.

### 3.3 Where `data_folder` / `project_folder` fit today

These aren't new concepts: `data_folder` corresponds to today's per-survey `knowledge_repo/`
(shared corpus, task #23) and `project_folder` corresponds to today's survey directory
(`survey.yaml` + `agents/` + `report/`). The config file's job is to let the CLI's `new`
subcommand know *where* to create these for a project that may contain multiple surveys over
time, rather than introducing a second storage format alongside the existing one.

### 3.4 The orchestrator agent: new concept, needs a new name

Your sketch wants "orchestrator agent detail (we need to set this up on UI as well where we can
setup agent card of orchestrator as well which runs the whole survey etc)". This is a new idea:
an Agent Card *for the thing that runs the survey*, not for a panel expert. Recommendation:
name this the **Conductor Agent** in code and UI (not "orchestrator agent"), specifically to
avoid colliding with the existing, already-shipped "orchestrator" (the survey-drafting assistant
behind `proposer.py`, task #15). Two different things both named "orchestrator" in the UI would
confuse every future session (including future me) reading this codebase.

Conductor Agent's Agent Card reuses the existing `AgentCard`/`ModelSpec` dataclasses unchanged
(same DID, same model spec fields) plus one new field, `responsibilities: List[str]` restricted
to the five Orchestration-Layer roles from your pipeline sketch (survey_generation,
task_planning, panel_selection, context_management, knowledge_distribution). No new dataclass
needed; this is an additive field on the existing `AgentCard`, not a fork of it.

**New UI**: a `ConductorAgentPage.jsx` (or a new tab inside `SettingsPage.jsx`, TBD at
implementation time; recommend a new top-level page since this is project-level, not
installation-level config, matching where `data_folder`/`project_folder` conceptually live) that
edits `orchestrator_agent.agent_card` through the same form components `AgentForm.jsx` already
provides for panel agents, filtered to the fields a Conductor Agent actually uses (model spec,
DID, responsibilities checklist) and omitting fields that only make sense for a panel expert
(personality/CV, see §4.3).

---

## 4. Four-layer pipeline: mapping your sketch onto (and extending) the real code

### 4.1 Researcher Layer: Prompt -> Requirements -> Survey -> Knowledge Base -> Research Goal

Maps onto: the `new` CLI subcommand (§2) plus a **new** requirements-extraction step that does
not exist yet. Today, `proposer.py` goes straight from prompt to draft `survey.yaml`; your
sketch inserts an explicit "Requirements" stage between Prompt and Survey. Recommendation: add
this as a new, inspectable JSON artifact (`requirements.json`: extracted research questions,
target population/domain, constraints) written to the project folder *before* survey generation,
so a user (or `--fix-survey`) can review/edit requirements without re-prompting from scratch.
This is a genuinely new artifact, not a renaming of something that exists.

### 4.2 Orchestration Layer: Survey Generator -> Task Planner -> Panel Selector -> Context Manager -> Knowledge Distributor

- **Survey Generator** = existing `proposer.py` orchestrator, unchanged.
- **Task Planner** = new. Today `run_survey()` runs every agent against every instrument level
  in a fixed order with no explicit plan artifact. A Task Planner step would decide *and record*
  agent-to-level assignment order, particularly relevant once §4.3's debate rounds mean not
  every agent necessarily answers every level in one pass.
- **Panel Selector** = existing Agent Library selection (`library.py`, task #14), already does
  this; no change needed beyond the Conductor Agent (§3.4) invoking it programmatically instead
  of a human picking from the UI, when `expert_agents.source: generate` is set in config (§3.2).
- **Context Manager** = existing per-agent RAG corpus + shared `knowledge_repo/` (task #23),
  already does this.
- **Knowledge Distributor** = existing knowledge-base linking (`knowledge_bases.py`,
  task #50), already does this.

Net new work in this layer is genuinely small: a Task Planner artifact and the Conductor
Agent's programmatic invocation path. Everything else already exists under a different label.

### 4.3 AI Panel Layer: agents with DID, Agent Card, CV, Personality, Tools, Knowledge

Existing `AgentCard` already covers DID, model spec ("Tools" via existing permissions/web-search
integration, task #23), and Knowledge (RAG corpus + knowledge-base links). Two fields from your
sketch do not exist yet: **CV** and **Personality**.

- **CV**: recommend a free-text or structured `credentials: List[str]` field (e.g. "PhD
  Biostatistics, 15 years clinical trial design") used only to enrich the system prompt's role
  description, exactly the same mechanism `agent_role_description` already uses — not a new
  subsystem, just a new AgentCard field that gets interpolated into the existing prompt template.
- **Personality**: recommend a small enum or short free-text `personality_notes` field (e.g.
  "skeptical of unvalidated instruments, prefers conservative confidence intervals") for the same
  reason: it shapes the system prompt, nothing else. Resist the temptation to build a separate
  "personality module" — this is prompt content, and the existing role-description mechanism
  already does prompt content well.

Both are additive `AgentCard` fields with no migration risk (old cards without them just get an
empty CV/personality section in the prompt).

### 4.4 Collaboration Layer: Independent Responses -> Reasoning Logs -> Multi-Agent Debate -> Consensus -> Confidence Estimation -> Evidence Collection -> Visualization -> Export

This is the layer with the most real, substantive new work, not just relabeling:

- **Independent Responses** = existing per-agent sampling in `run_survey()`. Already done.
- **Reasoning Logs** = existing QA post-check reasoning/sourcing log (task #29). Already done.
- **Multi-Agent Debate** = **does not exist**. Today agents answer independently with zero
  cross-agent visibility; there is no round where agent B sees agent A's reasoning and revises.
  This is the single largest genuinely new feature in the whole plan. Recommend implementing it
  as an optional second pass, gated by a `debate_rounds: N` survey.yaml setting defaulting to 0
  (off) for full backward compatibility with every existing survey: round 1 is today's
  independent-response behavior unchanged; if `debate_rounds > 0`, each subsequent round feeds
  every agent the prior round's anonymized reasoning logs (anonymized to avoid authority bias
  toward a specific agent's identity) and asks whether it wants to revise its answer.
- **Consensus** = new aggregation step on top of debate output: agreement metrics (e.g., how
  much the panel's weight distributions converged round over round), not a new elicitation
  mechanism — the existing BWM/AHP solvers already produce the point estimates; consensus is a
  new *report section* summarizing convergence, not a new solver.
- **Confidence Estimation** = **already exists** for the Bayesian hierarchical BWM path
  (`bwm_bayesian.BayesianResult`, 95% CI columns already rendered per `reporting.py`'s
  `_weight_table`). For the classical BWM/AHP paths, this needs the same treatment: bootstrap or
  cross-agent variance as a stand-in confidence interval where no Bayesian posterior exists.
  Post-debate, this should be recomputed over the *final* round's responses rather than round
  0's. Treat "debate tightens the credible interval" as an empirical claim to verify on a real
  survey, not an assumed benefit to advertise: multi-agent debate carries a real, documented risk
  of anchoring/groupthink (agents converging toward whichever position was voiced most
  confidently or first, rather than toward the truth), which looks identical to genuine consensus
  in the aggregate statistics. Before this feature is described as an improvement in any README
  or paper claim, run it on one existing survey and check whether the post-debate answers that
  changed did so for reasons visible in the debate transcript (citing a source or argument that
  actually addresses the disagreement) rather than simple conformity to the majority's initial
  answer.
- **Evidence Collection** = existing `sources_used` field per response (already collected,
  already validated per `hierarchical_bwm.py`'s parse-time check) plus the QA post-check log.
  Mostly already done; the new work is surfacing it more prominently in exports (§5).
- **Visualization** = existing PNG charts (`render_charts`, `render_hierarchical_bwm_charts`).
  Already done for the report; extending to Qualtrics/SPSS/DOCX/PDF exports is new (§5). If
  debate rounds ship, add one new chart type alongside the existing weight-distribution charts:
  a per-round position plot (x-axis: round number, y-axis: each agent's weight for a given
  criterion), so convergence or divergence across rounds is visible at a glance rather than only
  inferable from the numeric consensus metric.
- **Export** = the second largest genuinely new piece: only Markdown+PNG exists; DOCX, PDF,
  HTML, Qualtrics, SPSS, CSV do not (§5).

### 4.5 Priority ranking for implementation (recommended, not yet agreed with you)

Given the above, the actual new-code weight is concentrated in three places, not evenly spread
across four "layers": (1) multi-agent debate, (2) confidence estimation for non-Bayesian
instruments, (3) the export-format expansion. The rest is substantially existing functionality
that needs renaming/reframing in the UI and docs to match your layer vocabulary, which is cheap.
Recommend sequencing implementation in that order (debate -> confidence -> exports) since debate
changes the data shape every downstream consumer (reports, exports) needs to handle, so building
it first avoids re-touching the export code twice.

---

## 5. Export formats

Current state: Markdown (`report.md`) + PNG charts only, generated by `reporting.py`.

Target: Markdown, DOCX, PDF, HTML, Qualtrics, SPSS, CSV.

Recommendation, keeping with this project's own "always fully open source unless impossible"
rule (`.claude/rules/gitops.md` §6) and its "convert to a plain-text intermediary, never parse
proprietary formats directly" file-handling rule:

- **Markdown**: already done, stays the canonical source format every other export is generated
  *from*, not a peer format generated independently (single source of truth, no drift between
  export formats).
- **HTML**: generate via `markdown` (or `mistune`) rendering the existing `report.md`, wrapped in
  the CSS this project already committed to for the web UI’s look — cheapest new export, do it
  first.
- **PDF**: **reuse `text2officeprocessor`** rather than building a second Markdown-to-PDF path in
  this repo. That package already does templated, deterministic Markdown -> DOCX/PPTX/XLSX
  rendering and is already yours, already on PyPI-track, and already has tests; add it as an
  optional dependency (`agentic_survey[export]`) and call its documented Python API
  (`text2officeprocessor` is designed to be imported, not just CLI-invoked, per its `src/web`
  and `src/core` split) rather than reimplementing template-driven rendering.
- **DOCX**: same mechanism as PDF, via `text2officeprocessor`.
- **CSV**: straightforward — one row per (level, criterion, mean weight, CI bounds), generated
  directly from the already-computed solver output dict, no new dependency.
- **Qualtrics**: Qualtrics's own import format is a `.qsf` (Qualtrics Survey Format) JSON; open
  question for you (see §7) whether "export to Qualtrics" means (a) exporting the *instrument*
  (the BWM/AHP comparison questions) as an importable `.qsf` so a human panel could later
  complete the same survey Qualtrics-side, or (b) exporting *results* for Qualtrics-side
  analysis. These are very different features — (a) is a survey-authoring export, (b) is a
  results export — and your one-line mention doesn't disambiguate which.
- **SPSS**: SPSS reads `.sav` (binary) or plain `.csv`/`.tsv` with a companion syntax file
  defining variable labels. Recommend targeting **CSV + an SPSS syntax file** (`.sps`, plain
  text, defines variable/value labels) over the binary `.sav` format: `pyreadstat` (LGPL,
  genuinely open source, wraps the ReadStat C library) can write real `.sav` if binary output
  is later required, but starting with CSV+syntax avoids an extra binary-format dependency for a
  first release.

---

## 6. PyPI packaging plan (extends `docs/packaging-plan.md`)

Follow `docs/packaging-plan.md`'s Steps 1-3 largely as written (they're sound and already
reviewed), with these amendments now that the CLI design is concrete:

- **Framework**: `pyproject.toml`'s core dependencies gain `typer>=0.12.3` (§2.1), replacing the
  plan's implicit assumption of extending the existing argparse script.
- **Entry point**: `[project.scripts]` -> `symphysis = "agentic_survey.cli:app"` (Typer app
  object, not a `main()` function, matching `text2officeprocessor`'s
  `text2officeprocessor = "src.cli.main:main"` pattern adjusted for Typer's `app` convention).
- **Optional extras**: add `export = ["text2officeprocessor>=0.5.1"]` (§5) and
  `spss = ["pyreadstat>=1.2.0"]` alongside the plan's existing `web` extra.
- **Package name**: the plan leaves this as an open question (§ "Open questions for Dan" in that
  doc). Recommendation, since you're asking me to resolve ambiguities rather than leave every one
  open: publish as **`symphysis`** on PyPI (the product name, for discoverability — this is what
  people will search for) while the importable module stays `agentic_survey` (backward
  compatible with every existing survey folder's `PYTHONPATH=src` assumption and every existing
  `from agentic_survey import ...` call in this codebase). PyPI allows the distribution name and
  the top-level import name to differ (this is common — e.g. `pip install beautifulsoup4` imports
  as `bs4`); `[project.name] = "symphysis"` with `[tool.setuptools.packages.find] include =
  ["agentic_survey*"]` achieves exactly this.
- **CI/CD**: add a new `.github/workflows/publish.yml`, modeled directly on
  `text2officeprocessor/.github/workflows/python-publish.yml` (`release-build` + `pypi-publish`
  jobs, trusted-publisher OIDC, triggered on `release: types: [published]`), kept **separate**
  from the existing `ci-cd.yml` (which runs tests/lint on every push, task #46/#65's already-fixed
  workflow) rather than folding publish logic into it — publishing is a distinct, rarer,
  higher-stakes event that should not run on every push.
- **Testing before publish**: every new CLI subcommand needs a real-fixture test (this repo's
  existing convention per `tests/test_web_library.py`, not mocks). Before the first PyPI release,
  additionally verify the package installs and imports cleanly in a **clean virtualenv with only
  the published sdist/wheel installed** (`python -m build`, `pip install dist/*.whl` in a fresh
  venv, run a minimal `symphysis run` smoke test) — this catches the "works via `PYTHONPATH=src`
  in this repo but breaks when actually installed" class of bug the existing plan already flags.
- **Versioning**: first release `0.1.0`, matching `CITATION.cff`'s existing version field and the
  existing plan's recommendation against jumping to `1.0.0` pre-launch.

---

## 7. Open questions for you (genuinely yours to decide, not resolved above)

1. **Qualtrics export meaning** (§5): instrument-authoring export (`.qsf` for a human panel) or
   results export for Qualtrics-side analysis? These are different features.
2. **Debate round default**: confirmed as opt-in (`debate_rounds: 0` default) in §4.4 to avoid
   changing any existing survey's behavior silently — please confirm this default is right
   rather than defaulting debate *on*.
3. **Conductor Agent naming** (§3.4): I renamed your "orchestrator agent" to "Conductor Agent" to
   avoid colliding with the already-shipped survey-drafting orchestrator. If you'd rather rename
   the *existing* one instead (e.g. call it "Survey Drafter") and keep "Orchestrator" for the new
   runtime concept, that's a documentation/rename-only change, not a design change, and easy to
   flip before implementation starts.
4. **`symphysis` vs `agentic_survey` PyPI naming** (§6): I recommended publishing as `symphysis`
   with import name staying `agentic_survey`. Confirm before the first `pyproject.toml` commit,
   since renaming a published PyPI package after users have started depending on it is expensive.

---

## 8. Suggested implementation order

1. `pyproject.toml` + Typer migration of `cli.py` (§2, §6) — mechanical, low-risk, unblocks
   everything else being testable via the real CLI rather than only via the web UI.
2. Project-level config file + `symphysis new`/`fix-survey` subcommands (§2, §3) — the
   Researcher Layer.
3. Conductor Agent Agent Card + UI page (§3.4) — small, additive.
4. AgentCard CV/personality fields (§4.3) — small, additive, unlocks richer prompts immediately.
5. Multi-agent debate (§4.4) — the largest genuinely new feature; do this before touching export
   code, since it changes the data shape.
6. Confidence estimation for classical BWM/AHP (§4.4).
7. Export-format expansion: HTML first (cheapest), then CSV, then DOCX/PDF via
   `text2officeprocessor`, then SPSS syntax file, then Qualtrics (pending §7 question 1).
8. Documentation: a new `docs/cli-guide.md` and `docs/python-api-guide.md` (per your explicit
   ask for "good documentation for CLI and python docs"), plus updates to
   `docs/architecture/*.drawio` reflecting the four-layer pipeline vocabulary once the above is
   real, not speculative. For the Python API guide specifically: given `agentic_survey` is
   already fully type-hinted (dataclasses throughout) with substantial module-level docstrings
   explaining *why*, not just *what* (`agent_card.py`'s docstring is a good example already in
   the codebase), `pdoc` (zero-config, generates directly from docstrings, no separate `.rst`
   source tree to keep in sync) is the lowest-effort, highest-fidelity choice, matching how
   `text2officeprocessor` itself documents (a single hand-written `docs/guide.md`, not an
   auto-generated Sphinx/MkDocs site) — move to MkDocs later only if the project outgrows `pdoc`.
9. PyPI publish workflow + first clean-venv install test (§6) — last, once the CLI surface is
   stable enough that a published `0.1.0` is worth cutting.

---

## Appendix A: relationship to `docs/packaging-plan.md`

That document (already committed, `docs/packaging-plan.md`) covers the mechanics of making
`agentic_survey` installable and publishable. This document supersedes only its §2 CLI-subcommand
sketch (which didn't yet know your `new`/`--fix-survey`/four-layer-pipeline requirements) and
extends its "Open questions for Dan" with the package-naming recommendation in §6 above. Its
Steps 1 and 3 (installable package, PyPI publish mechanics) stand as written and don't need
re-litigating here.
