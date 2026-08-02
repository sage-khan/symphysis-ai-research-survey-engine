# Diagnostics

Bugs found, their root cause, and the fix. Kept separate from
`changelog.md` (which tracks what changed) so root causes stay easy to find
later.

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
