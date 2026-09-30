# Durable Decisions

Facts and decisions worth carrying across every future session, settled once
and not worth re-litigating. Not a diary (that's `.claude/sessions.md`); this
is the short list of things a fresh session needs to already know are true.

- **`memory.md`, `sessions.md`, and `tasks.md` all live under `.claude/`, not the repo root (2026-08-19).** Keeps the root clean for a project that may see open-source release, per this repo's own `project-details.md` roadmap.
- **No fabricated results, ever**: every reported sample must be a real completion from the provider named in its Agent Card. See `.claude/rules/project-details.md` for the full rule and why it exists.
- **No em dash (`—`), ever**, in anything written in Dan's voice. See `.claude/rules/writing-style.md`.
- **Documentation convention uses `docs/development/changelog.md` and `docs/development/diagnostics.md`** (a subfolder, unlike some sibling repos e.g. `creator-flow`, which uses a flat `docs/`). Don't cross-apply one repo's doc-path convention to the other.
- **This repo's Agent Card pattern (`src/symphysis/agent_card.py`: `did:key` identity, model/RAG/sampling/permissions spec, full run trace) is being reused as the agent-identity model for `creator-flow`'s own agents (research, script, media-gen, etc.).** If this file's structure changes, it may be worth telling `creator-flow` (see its `docs/plan.md` §4) since that plan cites this file directly.
