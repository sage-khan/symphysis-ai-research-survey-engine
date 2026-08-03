# Diagnostics

Bugs found, their root cause, and the fix. Kept separate from
`changelog.md` (which tracks what changed) so root causes stay easy to find
later.
## CI/CD still showed "no jobs run" after the line-1 YAML fix: a second schema error

**Found:** after quoting line 1's `name:` value (see the entry below), GitHub Actions still
reported no jobs running on push. Installed `actionlint` (not available in this environment by
default, downloaded the release binary directly) and ran it against the workflow file directly,
which a plain `yaml.safe_load()` cannot catch since the YAML itself is syntactically valid;
this is a GitHub-Actions-schema-level error, not a YAML-level one.

**Root cause:** the `deploy` job's `environment.url` field referenced `secrets.SYMPHYSIS_SERVER_HOST`.
The `environment.url` field only allows a specific, narrower set of contexts (`env`, `github`,
`inputs`, `job`, `needs`, `runner`, `strategy`, `vars`, `steps`); `secrets` is not among them.
GitHub Actions validates a workflow's entire job graph before running anything, so one job
having an invalid expression in a disallowed context appears to fail the whole run at the
validation stage, exactly matching "no jobs were run" rather than "one job failed."

**Fix:** removed the `url:` line from the deploy job's `environment` block (a purely cosmetic
convenience link in the GitHub UI's Environments view, not required for the deploy step itself
to run). `actionlint` now reports zero errors. The identical root-cause bug (the line-1 quoting
issue only, this repo's own deploy workflow never had the `secrets`-in-`environment.url`
mistake) was also found and fixed in `project-cogtwins`'s `ci-cd.yml`, which this repo's
workflow was modeled on.

## The shared default system prompt template hardcoded one survey's domain for every survey

**Found:** writing `docs/getting-started.md`'s walkthrough with a deliberately non-construction
example survey (three generic SRE failure modes), then reading the actual prompt an agent
received: it opened with "You are completing a structured Best-Worst Method expert-elicitation
survey for a construction-industry blockchain suitability framework (the Blockchain Suitability
Index, BSI)", regardless of the survey actually being run.

**Root cause:** `config/prompts/expert_panel_system.txt`, the file every agent card falls back
to (`web/backend/routers/agents.py`'s `DEFAULT_PROMPT_TEMPLATE`) unless it names a different
`system_prompt_template`, had BSI/construction wording baked into its shared default text, not
just into `bsi-hawc-bwm`'s own survey-specific rulefile and knowledge_repo (which correctly do
name BSI/construction, since that survey really is about BSI/construction). Any other survey
created without explicitly overriding this field, including through the web UI's New Survey
form, silently told every one of its agents it was doing BSI construction work.

**Fix:** genericized the shared default template's wording (now: "the specific criteria, their
meaning, and the survey's subject matter are given to you below, in the task itself and in any
rules or reference material provided alongside it"), which loses nothing for `bsi-hawc-bwm`
specifically since its actual domain framing already comes from its own rulefile, knowledge_repo
primer, and the instrument's own per-level criterion descriptions, none of which depend on this
shared file's wording. 164/164 tests pass (none asserted on the old hardcoded string).

## qwen2.5:32b still rated Best-to-itself as 9 on L1 with the ratio rule stated once, up front

**Found:** after swapping to qwen2.5:32b (see the entry above), re-ran and checked
blockchain-engineer-base-ollama's fresh output specifically (isolated from older, accumulated
batches in the same conversation.jsonl by its own qa_precheck timestamp, since a separate
tooling issue, described below, meant the file was never actually cleared between runs): 12 of
15 attempts still failed with `Level 'L1': best_to_others[best] must be 1, got 9`. The
ratio-vs-score rule was confirmed present in the exact prompt this agent received. L1 was the
only level with this failure; L2 through L3e, further from the rule statement in the prompt,
mostly succeeded at it.

**Root cause:** the ratio rule was stated once, in the shared intro, before all seven levels;
each level's own task text only pointed back to it ("see the ratio rule above"). L1 being the
level closest to that statement, not the farthest, ruled out "the rule faded from context" as
the explanation; something about L1 specifically (its four abstract, headline-sounding
criteria: Data Value Score, Technical Feasibility Fit, Economic Value, Attack Resistance) seems
to prime a "this is the most important decision, rate it emphatically" response that overrides
a rule stated once and only referenced, not restated, at the point of generation.

**Fix:** `instruments/hierarchical_bwm.py`'s per-level task template now restates the
self-comparison-is-1 rule locally, inline, for every level ("a ratio, not an importance score,
so Best-to-itself is exactly 1, never 9"), instead of only pointing back to the shared intro.
Deliberately kept in lowercase ("a ratio") rather than repeating "RATIO" in capitals seven
times, so the existing regression test asserting the canonical rule statement appears exactly
once still holds.

## docker exec's glob was expanded by the host shell, not the container's, so cleanup silently no-op'd

**Found:** while trying to isolate a specific run's rejection data, found the same agent's
`conversation.jsonl` contained multiple batches from different runs/models concatenated
together, even though each run was preceded by an explicit cleanup command.

**Root cause:** the cleanup was run as `ssh host "docker exec <container> rm -rf /app/surveys/.../*/conversation.jsonl"`.
The `*` glob is expanded by whichever shell first parses the command line, here the remote
host's own login shell (since the whole `docker exec ...` string is one argument to the outer
`ssh`), not a shell running inside the container. `/app/...` does not exist on the host
filesystem (it is a path inside the container's own filesystem namespace), so the host shell's
glob matched nothing and, per default (non-nullglob) bash behavior, passed the literal
unexpanded string `*/conversation.jsonl` through to `rm -rf` inside the container, which
silently found no file by that literal name (`-f` suppresses the "no such file" error) and
deleted nothing.

**Fix:** wrap the remote command in an explicit `bash -c '...'` so glob expansion happens
inside the container's own shell, where `/app/...` is real: `docker exec <container> bash -c
'rm -rf /app/surveys/.../*/conversation.jsonl ...'`. This is an operational mistake in how the
cleanup was invoked from outside the app, not a bug in Symphysis's own code; noted here because
it directly caused several minutes of misdiagnosis (attributing a fresh model's behavior to
stale leftover data from an earlier run) before being caught.

## Every small/mid local Ollama model failed the full seven-level hierarchical_bwm task

**Found:** after fixing max_tokens and the ratio-vs-score prompt warning (see the entry above),
re-ran the survey and every completed Ollama-backed agent still showed zero_accepted. Checked
each one's raw completion / rejection log directly:

- `gemma4:26b` (compliance-officer): degenerated into an infinite repetition loop
  (`{"L1": {"L1": {"L1": {...` nested hundreds of levels deep) on every one of 15 attempts,
  hitting max_tokens on pure repetition, not real content. A model-capability failure, not a
  prompt-clarity or token-budget one.
- `qwen2.5:14b` (bim-coordinator): still rated Best-to-itself as 9 on L1 in 12/15 attempts even
  with the explicit "never 9" warning now in the prompt (confirmed present in the running
  container's actual file). An instruction-following limit at this model size for this specific
  task, not a missing instruction.
- `deepseek-r1:14b` (blockchain-engineer): consistently malformed JSON (missing delimiters,
  unterminated objects) despite the larger token budget.
- `phi4:14b` (data-engineer): a mix of missing ratings for several criteria and non-integer
  decimal ratings (e.g. `others_to_worst[V]=1.8`) instead of the required 1-9 integers.

**Root cause:** the seven-level bundled response `hierarchical_bwm` asks for in one call is
simply too long and structurally demanding a generation task for these 7B-26B local models,
independent of the specific fixes already applied. This is a capability ceiling, not a further
prompt-wording gap.

**Fix:** moved every local-model role in `bsi-hawc-bwm` (BIM Coordinator, Blockchain/DLT
Engineer, Compliance Officer, Data Engineer, Construction Project Manager, Structural Engineer;
both their base and RAG variants) to `qwen2.5:32b`, the only meaningfully larger model already
pulled on the veritas server. Agent identity (DID, seed derivation) is keyed to `agent_id` and
survey id, never model name, so this is a pure model swap with no identity drift. If
`qwen2.5:32b` also proves unreliable at this task, the next escalation is splitting
`hierarchical_bwm` into one call per level (matching the flat `bwm` instrument's
proven-reliable single-level shape) rather than trying still-larger models indefinitely.

## hierarchical_bwm agents had every sample rejected: max_tokens left over from the old flat-BWM survey

**Found:** running the newly-converted bsi-hawc-bwm survey (see the hierarchical BWM changelog
entries), every Ollama-backed agent showed `zero_accepted` in `/analytics`, several with
malformed-JSON rejection reasons ("Expecting ',' delimiter", "No JSON object found in
response"). Checked one agent's raw completion log directly: `"finish_reason": "length"`, with
the response cut off mid-way through the very first level's `reasoning` field.

**Root cause:** every agent card in this survey still had `model.max_tokens: 1024`, sized for
the old flat `bwm` instrument's single-level response (one best/worst pick plus up to six
1-9 ratings each way, comfortably under 1024 tokens). `hierarchical_bwm` asks for the same
shape seven times in one response (L1 through L3e) plus a reasoning sentence per level; the
real response is several times longer than what these agents were ever configured to produce,
so Ollama's `num_predict` (which `max_tokens` maps to directly) cut every response off before
the JSON object closed.

**Fix:** raised `model.max_tokens` to 6144 across every agent in this survey. Also relevant but
not the primary cause: `deepseek-r1:14b` is a reasoning model whose visible completion can
include a chain-of-thought preamble before its final JSON, which eats further into a small
token budget; the more generous ceiling covers this too. Re-run and re-check `/analytics`
after any future instrument change that meaningfully lengthens the expected response shape,
rather than assuming an existing per-agent `max_tokens` value still fits.


## CI/CD workflow YAML was invalid, blocking every run since it was added

**Found:** GitHub Actions showed "Invalid workflow file: .github/workflows/ci-cd.yml#L1 -
You have an error in your yaml syntax" on every push since the workflow was created, so it
never actually ran validate/test/deploy despite existing in the repo.

**Root cause:** line 1 was `name: CI/CD: Symphysis`, an unquoted scalar value containing its
own `: ` (colon-space). YAML parses `key: value`, and a colon-space inside an unquoted value
is itself read as the start of another mapping, which is a parse error one level in. Confirmed
with `yaml.safe_load()` locally: `mapping values are not allowed here, line 1, column 12`.

**Fix:** quote the value: `name: "CI/CD: Symphysis"`. Verified the whole file parses and the
three expected jobs (`validate`, `test`, `deploy`) are present.


## Bayesian BWM concentration hyperprior was too informative

**Found:** verifying `bsi-survey-app`'s Bayesian BWM solver line-by-line
against the original author's (Majid Mohammadi) reference JAGS
implementation (`github.com/Majeed7/BayesianBWM`) before adopting it as this
app's solver.

**Root cause:** the reference model's concentration hyperprior is a
diffuse, near scale-free `Gamma(0.01, 0.01)` (mean approximately 1). The
ported implementation used `Gamma(1, 0.01)` (mean 100), which is
materially more informative and biases the posterior toward artificially
narrow credible intervals, i.e. toward looking more confident about expert
agreement than the data supports.

**Fix:** `solvers/bwm_bayesian.py` uses `Gamma(0.01, 0.01)`, matching the
reference model. Verified with a real PyMC/NUTS run: credible intervals are
non-degenerate after the fix.

## Ollama request timeout too short for a multi-model roster

**Found:** live end-to-end test on the veritas server running the 6-model
Ollama roster (Qwen, Gemma, Llama, Mistral, DeepSeek, Phi); hit
`ReadTimeout` at 300s.

**Root cause:** switching between several distinct models in one survey
makes Ollama cold-load each one from disk on its first request, and a
reasoning model (`deepseek-r1`) can spend a long time on chain-of-thought
before its final answer. `requests.post(..., timeout=300)` was hardcoded.

**Fix:** `providers/ollama_provider.py` defaults to 900s, configurable via
`OLLAMA_TIMEOUT_SECONDS`.

## A single uncredentialed or misconfigured agent crashed the whole survey

**Found:** while adding the Claude/manual "independent reviewer" tier;
running the full roster without `ANTHROPIC_API_KEY` set anywhere crashed
`run_survey` entirely at the first Claude agent.

**Root cause:** `orchestrator.py`'s per-agent loop had no error handling
around `Agent(...)`/`agent.run(...)`; any `ProviderError` (missing API key),
`PermissionError_`, or `AgentCardError` propagated up and killed the
process, discarding whatever other agents had already succeeded.

**Fix:** those three exception types are now caught per-agent, logged as a
"skipped" notice (distinct from a pending manual response, which is
expected and self-resolves), and the run continues with whichever agents
did work. Regression tests in `tests/test_orchestrator.py`.

## Two Ollama model families misread the BWM self-comparison convention

**Found:** the same 6-model roster test; `llama3.1:8b` and `gemma4:26b`
returned 0/5 accepted samples each despite the prompt already stating
"including Best itself, which must be 1."

**Root cause:** both models rated Best-to-itself as 9, i.e. read the 1-9
scale as an absolute importance score ("Best is the most important, so
rate it 9") rather than a ratio ("Best is exactly one time as important as
itself"). Not a solver or guardrail bug: the guardrails correctly rejected
every one of these malformed responses and never fabricated a fallback;
this was a prompt-clarity gap.

**Fix:** `instruments/bwm.py`'s default task template adds an explicit
ratio-vs-score explanation and a worked example using placeholder criteria
(X/Y/Z, chosen to not collide with real dimension codes such as "C" for
Criticality).

## Manual provider's index inference skipped a just-answered sample (two bugs, same root cause)

**Found (first time):** writing `tests/test_manual_provider.py`.

**Root cause:** `_next_index` inferred "which sample is this" purely from
which `prompt_NN.md`/`response_NN.txt` files already existed on disk. Two
sequential `complete()` calls for the same agent within one process (as
`run_with_guardrails` makes for `repeats > 1`) could not distinguish
"return the answer I was just given" from "move on to the next question"
once both files existed for the current index, so it silently skipped past
a freshly-answered sample instead of returning it.

**First fix (incomplete):** replaced file-state inference with an explicit
per-directory module-level call counter, so N sequential calls in one
process visit index 0, 1, 2, ... in order regardless of what's already on
disk.

**Found (second time):** live end-to-end test of the web UI. A CLI
invocation is a fresh process every time, so a counter that must reset
exactly once per `agent.run()` call happens to reset for free. The web
backend is a long-lived process: clicking "Run survey" a second time (after
pasting a manual response) reuses the same process, so the counter had
already advanced past index 0 from the first click and never revisited it,
reporting "still waiting on sample 1" forever even after sample 0's answer
was pasted and consumed.

**Second fix (correct):** removed the module-level counter entirely.
`guardrails.run_with_guardrails` already knows which sample index it is
asking for on each loop iteration; it now passes `sample_idx` explicitly to
the provider (only for providers that opted in via `extra_call_kwargs`,
currently just `manual`), so the provider needs no state of its own at all.
No assumption about process lifetime to violate.

## Chart rendering crashed on a negative error-bar value

**Found:** `pytest` failure in `test_orchestrator.py` after a fresh
`pip install` pulled a newer matplotlib than had been used before (which
tightened its `yerr` validation), then reproduced live against real data:
a single-agent `mistral:7b` run against the veritas server's Ollama
produced `agg_ci_lower[0] = 0.5289173888573906` fractionally *above*
`agg_mean[0] = 0.5289173888573904`.

**Root cause:** `render_charts` (`reporting.py`) computed each error-bar
half as `mean - ci_lower` / `ci_upper - mean` with no floor. With very few
effective samples (a one-agent panel, or any criterion whose bootstrap
draws collapse to a single value, see `solvers/bwm_bayesian.solve_bootstrap`
with `K=1`), the mean and the 2.5th/97.5th percentiles are computed from
the same identical values by two different floating-point code paths
(`np.mean` vs `np.percentile`) and can disagree by a few ULPs, landing the
"lower" bound a sliver above the mean. matplotlib rejects any negative
`yerr` outright rather than clamping it, so this crashed chart generation
after `report.md` and `combined_results.json` had already been written,
so a run with perfectly valid results still surfaced as a hard failure.

**Fix:** `reporting.py` clips each error-bar half to `max(0.0, ...)` before
passing it to `ax.bar`. Verified: the exact production values above render
without error, and the full test suite (41 passed, 1 skipped) is green.

## Every RAG-enabled agent was silently skipped: corpus root never matched its own scope

**Found:** live end-to-end run on the veritas server (2026-08-03), a fresh
17-agent panel built for the TrustRouter survey uploaded from the real
LimeSurvey 185662 export. All six base-Ollama agents produced samples in
order; every RAG-enabled sibling (`*-rag-ollama`) was silently absent, with
no error printed and no `conversation.jsonl` ever written for it, jumping
straight to the next agent in the roster.

**Root cause:** `Agent.__init__` (`agent.py`) calls
`check_data_scope(card.rag.corpus_path, card.permissions)` with the RAG
corpus *root* path (e.g. `surveys/<id>/rag_corpora/bim-coordinator`, no
trailing slash) before ever reading a file inside it. Every shipped example
card, the web UI's `create_agent` default, and the README's own sample
Agent Card grant that corpus via a `<root>/**` scope. `fnmatch(path, scope)`
requires a literal `/` after `<root>` to satisfy a `/**` suffix, so the bare
root path, which has no trailing slash, never matched its own scope.
`check_data_scope` therefore raised `PermissionError_` for every single
RAG-enabled agent ever created via the documented pattern, which
`orchestrator.py`'s per-agent exception handling correctly (per its own
design) logs as "skipped" and continues past, so the failure was silent
by design, not a crash, and easy to miss without checking each agent's
runtime folder individually. The existing unit tests for
`check_data_scope` never caught this because they only ever passed a *file
path inside* the corpus (`.../bim-coordinator/SOURCES.md`), never the bare
corpus root that `agent.py` actually passes.

**Fix:** `permissions.py`'s `check_data_scope` now also treats a scope
ending in `/**` as covering its own base directory (the literal string with
`/**` stripped), not just paths under it. Two new regression tests added to
`tests/test_permissions.py` (`test_check_data_scope_allows_the_corpus_root_itself`,
`test_check_data_scope_rejects_a_different_roots_bare_path`). Full suite:
46 passed. Verified live: re-running the same 17-agent panel after the fix
produced real, non-empty `conversation.jsonl`/`samples/` output for the
RAG-enabled agents that had previously been silently skipped.

## .gitignore's runtime-exclusion list was missing card.json

**Found:** staging the live-run survey's files for commit; every agent's
runtime folder brought in a duplicate `card.json` (storage.init_agent's
"copy of the card actually used for this run") even though the source
config at `agents/<id>.json` was already tracked.

**Root cause:** the .gitignore comment states the intent plainly ("keep the
example survey's configs tracked but not the per-agent runtime folders it
produces"), and lists 7 of the 8 runtime files storage.py writes, but
`card.json` was missing from the list.

**Fix:** added `surveys/*/agents/*/card.json` to .gitignore.
