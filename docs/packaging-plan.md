# Packaging plan: PyPI package and CLI

A plan to review before implementation, following the README's "Future enhancements" ->
"Packaging" section (already tracked there as `symphysis` CLI and an installable
`agentic_survey` package). This assumes the launch-readiness work (LICENSE, CITATION.cff,
CONTRIBUTING.md) is already in place, since a package published to PyPI needs the same license
clarity a public repository does.

## What already exists to build on

- `src/agentic_survey/cli.py`: a real, working CLI already, just with one subcommand
  (`run <survey_dir>`). This is the precursor, not a rewrite target.
- `pyproject.toml`/`setup.py`: neither exists yet. `requirements.txt` and
  `web/backend/requirements.txt` are the only dependency declarations today, both meant for
  `pip install -r`, not for a proper installable package.
- The package boundary is already reasonably clean: `src/agentic_survey/` (the core engine:
  Agent Cards, providers, instruments, guardrails, solvers, RAG) versus `web/` (the FastAPI
  backend and React frontend, which depend on the core package but are not required to use it).

## Step 1: make `agentic_survey` a real installable package

- Add `pyproject.toml` using the standard `[build-system]` + `[project]` metadata (PEP 621),
  not a `setup.py`, since that's the current, actively-recommended approach and avoids a
  separate `setup.cfg`.
- Declare the core dependencies `agentic_survey` actually needs at import time (PyMC, numpy,
  requests, PyYAML, and whichever RAG dependencies are load-bearing rather than optional) as
  `[project.dependencies]`; keep genuinely optional pieces (sentence-transformers, the FastAPI
  web stack) as `[project.optional-dependencies]` extras, e.g. `pip install agentic_survey[web]`
  for the full app, plain `pip install agentic_survey` for just the engine.
- Version the package from `CITATION.cff`'s `version` field (or vice versa: pick one source of
  truth and keep the other in sync) so a release doesn't require updating the version in two
  unrelated places and forgetting one.
- Verify `import agentic_survey` and a minimal `run_survey()` call work from a clean virtualenv
  with only the published package installed, not from inside this repository's own working
  directory relying on `PYTHONPATH=src`, since that's exactly the difference between "works
  when cloned" and "works when installed."

## Step 2: a real `symphysis` CLI entry point

- Add a `[project.scripts]` entry (`symphysis = "agentic_survey.cli:main"`) so
  `pip install agentic_survey` gives a `symphysis` command on the PATH, not just a Python
  module invoked via `-m`.
- Extend `cli.py` beyond its current single `run` subcommand to cover the operations the web
  UI already supports, so the CLI is a first-class alternative to the web UI, not a stripped-down
  fallback: `symphysis new <survey-id>` (scaffold a `survey.yaml` and `agents/` directory),
  `symphysis add-agent` (create an Agent Card interactively or from a template, mirroring the
  Agent Library's fields), `symphysis run <survey-dir>` (already exists), and
  `symphysis report <survey-dir>` (regenerate the report/charts from already-accepted samples
  without re-running the whole survey, useful after manually editing a rulefile or fixing a
  malformed response by hand).
- Every new subcommand needs its own test, following this repo's own existing test conventions
  (real temp-directory fixtures, not mocks, per `tests/test_web_library.py`'s stated rationale).

## Step 3: publish to PyPI

- Reserve the package name (`agentic_survey` may already collide with something on PyPI;
  check before assuming it's available, and have a fallback name, e.g. `symphysis-survey-engine`
  or `agentic-survey-engine`, ready).
- Publish via GitHub Actions on a tagged release (`git tag v0.1.0`, a new CI job triggered on
  tag push, using PyPI's trusted-publisher OIDC flow rather than a long-lived API token stored
  as a secret, since that avoids ever having a PyPI credential sitting in this repo's secrets at
  all).
- A first PyPI release should be `0.1.0` or lower (`0.0.x`) to signal pre-1.0 API instability
  honestly, matching the CITATION.cff version already in place, not jump straight to `1.0.0`
  before the API has had any real external users.

## What this plan deliberately does not cover yet

- Publishing the web UI itself as an installable artifact (it stays a clone-and-run Vite/FastAPI
  app for now; only the core `agentic_survey` engine and its CLI are in scope for PyPI).
- A hosted/managed version of Symphysis (explicitly a later-stage item on the monetization
  ladder in the IP strategy analysis, not part of this packaging work).
- Kubernetes packaging (`infrastructure/kubernetes/` is a separate, currently-empty
  placeholder; a Helm chart or manifest set would be its own follow-up, not blocked by or
  blocking this PyPI work).

## Open questions for Dan

- Is `agentic_survey` the name to publish under, or does the public-facing product name
  (`symphysis`) belong in the PyPI package name too, for discoverability, even though the
  internal import name would stay `agentic_survey` for backward compatibility with every
  existing survey folder's `PYTHONPATH=src` assumption?
- Should the CLI's new subcommands (`new`, `add-agent`, `report`) ship in the same first release
  as the PyPI package itself, or should the first release be `run`-only (matching what already
  exists and is tested today) with the richer CLI as a fast follow-up once the package itself is
  confirmed to install and import cleanly for someone outside this repository?
