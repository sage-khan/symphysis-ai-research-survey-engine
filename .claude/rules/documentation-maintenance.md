# Documentation Maintenance (mandatory, every code change)

This repo has exactly two narrative documentation surfaces at the root
level: `README.md` (what the repo is, how it works, how to set it up, what
every main file does, the repository structure) and
`docs/development/changelog.md` (what changed, when, and why), paired with
`docs/development/diagnostics.md` (bugs found, root cause, fix) per
`software-directory-structure-guide.md`'s documentation convention. Nothing
else in this repo narrates "what changed" -- there is deliberately no
per-feature status doc, no `NOTES.md`, no second README in a subdirectory.

## The rule

**Any commit that adds, removes, renames, or meaningfully changes a file,
module, endpoint, CLI command, environment variable, or workflow described
in `README.md` must update the relevant section of `README.md` in the same
change.** Do not defer this to a follow-up commit and do not treat it as
optional polish -- an out-of-date README is actively misleading (it tells
the next reader, human or AI, to run a command that no longer exists, or
fails to mention one that now does) and is a documentation *defect*, per
this repo's own `software-directory-structure-guide.md`: "Outdated
documentation is treated as a defect."

**Any change worth a commit is worth a `changelog.md` entry.** Add a dated
entry (`## YYYY-MM-DD (short topic tag)`, following the existing entries'
format) describing what changed and, briefly, why. If the change was a bug
fix, also add a `docs/development/diagnostics.md` entry: found (how/when),
root cause, fix -- this repo has a documented history of the same root
cause being independently rediscovered when it wasn't logged (see the
manual-provider sample-index bug's two separate discovery entries in
`diagnostics.md`), which wastes real time.

## What specifically to check in README.md before considering a change done

- **"Repository structure" tree and the three "main files" tables**
  (core package / web backend / web frontend): if a file was added, removed,
  or renamed, or its responsibility changed enough that its one-line
  description in the table is no longer accurate, update it.
- **"Setup" / "Web UI setup" / "Remote-LLM mode"**: if a command, flag,
  environment variable, or endpoint changed, update the exact command
  shown, don't leave a stale one next to the new behavior.
- **"How it works" pipeline diagram**: if the call sequence between
  `agent_card` -> `Agent` -> `providers` -> `instrument` -> `guardrails` ->
  `storage` -> `solvers` -> `reporting` changes (a new stage inserted,
  removed, or reordered), update the diagram, not just the prose elsewhere.
- **"Status / what's deferred"**: if a change closes one of the listed
  deferred items, remove it from that list (don't leave a "TODO" that's
  already done, which misdirects future work).

## Why this is its own rule file, not folded into project-details.md

`project-details.md` describes this project's *relationship* to
VERITAS/BSI-TrustRoute/CogTwins (context that changes rarely). This rule is
about a *process* that applies to every change regardless of what that
change is about, so it needs to be checked every time, not just read once
for context. Keeping it separate makes it easy to point at directly: "see
`documentation-maintenance.md`" is unambiguous in a way "see
`project-details.md`, the process bit near the bottom" is not.
