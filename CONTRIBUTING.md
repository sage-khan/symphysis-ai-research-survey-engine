# Contributing to Symphysis

Thanks for considering a contribution. This is a young, actively
developed research tool; the process below is intentionally lightweight.

## Getting set up

```bash
git clone https://github.com/sage-khan/symphysis-ai-research-survey-engine
cd symphysis-ai-research-survey-engine
pip install -r requirements.txt -r web/backend/requirements.txt
```

See `docs/getting-started.md` for two runnable walkthroughs (one needs no
external accounts at all) and the README's "Setup" section for running
the web UI.

## Before opening a pull request

1. **Run the test suite.**

   ```bash
   PYTHONPATH=src:web python -m pytest tests/ -q
   ```

   Every new instrument, solver, or backend endpoint should come with
   tests exercising its real behavior, not just a smoke test. See any
   existing `tests/test_*.py` for the pattern this repo already uses
   (real temp-directory fixtures over mocks where practical).

2. **Lint.**

   ```bash
   pip install ruff==0.4.7
   ruff check src/ web/backend/ --select E,W,F --ignore E501,E402
   ```

   This is the exact check CI runs (`.github/workflows/ci-cd.yml`); a
   pull request that fails it will fail CI too.

3. **Update the docs in the same change**, not as a follow-up. If your
   change adds, removes, renames, or meaningfully alters a file, endpoint,
   or workflow described in the README, update the relevant README
   section and add a dated entry to `docs/development/changelog.md` (plus
   a `docs/development/diagnostics.md` entry if it's a bug fix). See
   `.claude/rules/documentation-maintenance.md` for the full rule this
   project holds itself to on every change, human or AI-assisted.

## What a good pull request looks like

- **One logical change.** A new instrument, a UI fix, a bug fix: pick one.
  Don't bundle an unrelated refactor into the same diff.
- **Real tests, not fabricated ones.** If you're adding a provider,
  instrument, or solver, exercise its actual behavior; don't just assert
  that a function was called.
- **No secrets, no dummy data left unmarked.** If a change genuinely needs
  a placeholder value during development, mark it clearly in a code
  comment so it's easy to find and replace later; never commit a fake API
  key, credential, or invented dataset as if it were real.
- **Open source by default.** When a change needs a new library, service,
  or infrastructure component, default to a fully open-source option end
  to end; if you conclude none exists for a specific requirement, say so
  explicitly in the pull request description.

## Where to file issues

Open a GitHub Issue on this repository for bugs, feature requests, or
questions. Include, for a bug report: what you ran, what you expected,
what actually happened, and (if it's a survey run) the relevant
`/analytics` output or trace log excerpt rather than just "it didn't
work."

## Code of conduct

Be direct and be kind; disagree about ideas, not people. Anything short
of that (harassment, personal attacks, discriminatory language) will get
your access revoked, no warning cycle needed.
