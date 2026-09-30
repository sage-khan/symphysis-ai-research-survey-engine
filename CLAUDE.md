# CLAUDE.md — Symphysis

## Agent and subagent concurrency

**Never launch more than 2 Agent/Task subagents at once without asking the user first.** Never fire off a fresh batch until the prior ones have finished, or the user has explicitly said it's fine to proceed. This includes a task that is itself known to internally fan out into further parallel subagents (e.g. graphify's semantic-extraction step spawning several chunk subagents per repo) — count those toward the total too, not just the top-level launches.

**Why this is a hard rule, not a preference:** on 2026-08-31, launching 8 parallel background agents at once (running the graphify knowledge-graph pipeline across this repo and sibling project repos) exhausted the account's Anthropic API session usage cap, and every in-flight agent failed mid-task. The user's own words at the time: "next time ask if you want to spawn more than 2 agents... I want all the work done but when you run the agents, it fucks up my complete usage count. already anthropic has fucked up the token limits." Usage headroom on this account is a real, already-strained resource, not something to spend freely on parallelism.

**How to apply:** Before launching Agent/Task calls, count how many are about to go out in that one message. If the total is more than 2, stop and ask whether to proceed at that concurrency or to batch the work (2 at a time, waiting for completion between batches) instead.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
