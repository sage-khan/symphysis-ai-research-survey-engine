can you compare open mono ai , claw code, open code and claude code for me? I use claude code alot but i need an open source version to build good agent harnesses etc for my open source tool called symphysis (pypi) to allow for agent spawning that is governed by agent passport and with ecvetyhing logged (thinking ,tool call etc ). 

Yes. For **Symphysis**, I would not choose purely on "which one is most like Claude Code." Your actual requirement is more specific:

> **A model-agnostic agent execution substrate where Symphysis owns identity, spawning, policy, isolation, and audit, while the underlying harness handles the agent loop, tools, context management, and model interaction.**

That changes the ranking substantially.

I checked the current projects and, importantly, your current Symphysis architecture. Symphysis already has portable Agent Cards, `did:key` identities, provider allowlists, data-scope enforcement, guardrails, raw completion logging, and agent spawning concepts. ([PyPI][1])

## My conclusion

For your use case:

**1. OpenCode. Best execution substrate/reference architecture**
**2. Claw Code Agent by HarnessLab. Best Python-native reference for what you are trying to build**
**3. OpenMonoAgent. Interesting, particularly for local-first execution, but too opinionated**
**4. Claude Code. Still the benchmark for agent quality, but not the foundation for an open Symphysis runtime**

The important nuance is that I would **not make OpenCode itself the security authority**. I would make **Symphysis the control plane** and treat OpenCode or another harness as a worker/runtime.

---

# 1. The architecture I think you actually want

Something like this:

```text
                    SYMPHYSIS CONTROL PLANE
       ┌────────────────────────────────────────────┐
       │                                            │
       │  Agent Passport / DID / Credentials        │
       │  Policy Engine                             │
       │  Spawn Authority                           │
       │  Budget / Quota                            │
       │  Identity + Lineage                        │
       │  Audit / Event Store                       │
       │  Approval / Trust Decisions                │
       │  Isolation / Sandbox Policy                │
       │                                            │
       └───────────────────┬────────────────────────┘
                           │
                    "Spawn Agent"
                           │
                  Passport validated
                           │
             ┌─────────────┴─────────────┐
             │                           │
       OpenCode runtime            ClawCode runtime
       / other harness             / custom runtime
             │                           │
       ┌─────┴────────┐          ┌──────┴─────────┐
       │ agent loop   │          │ agent loop     │
       │ tools        │          │ tools          │
       │ MCP          │          │ MCP            │
       │ context      │          │ context        │
       │ model calls  │          │ model calls    │
       └─────┬────────┘          └──────┬─────────┘
             │                           │
             └───────────┬───────────────┘
                         │
                  Event stream
                         │
               ┌─────────▼─────────┐
               │ Symphysis Audit   │
               │                  │
               │ spawn             │
               │ prompt            │
               │ model call        │
               │ reasoning summary │
               │ tool requested    │
               │ policy decision   │
               │ tool execution    │
               │ result            │
               │ child spawn       │
               │ completion        │
               └───────────────────┘
```

That separation is much more interesting than simply cloning Claude Code.

---

# 2. Claude Code

Claude Code remains the thing I would use as the **behavioral benchmark**.

Its Agent SDK exposes built-in tools, subagents, MCP, sessions, permissions and hooks. The hook system is particularly mature. You can intercept `PreToolUse`, `PostToolUse`, `SubagentStart`, `SubagentStop`, compaction, permission requests, session lifecycle events, etc. ([Claude][2])

That is extremely close to what you want.

For example:

```text
PreToolUse
      ↓
 Symphysis policy
      ↓
 allow / deny / modify
      ↓
 tool execution
      ↓
PostToolUse
      ↓
 audit event
```

Claude Code also has explicit subagent lifecycle hooks, which is excellent for lineage tracking. ([Claude][3])

### Where Claude Code loses

The obvious problem is that Claude Code is not an open-source runtime. The repository is distributed under Anthropic's commercial terms rather than an OSI open-source license. ([GitHub][4])

So I would **not** build Symphysis around Claude Code internals.

Instead:

**Use Claude Code to determine what a world-class harness should behave like.**

That distinction matters.

---

# 3. OpenCode

This is the strongest candidate.

OpenCode is MIT licensed and explicitly designed as an open-source, provider-independent coding agent. It supports Anthropic, OpenAI, Google, local models and other providers. It also has a client/server architecture rather than being purely a terminal application. ([GitHub][5])

More importantly for you, its extension points are unusually good.

OpenCode plugins can subscribe to:

```text
command.executed
file.edited
message.updated
permission.asked
permission.replied
session.created
session.compacted
session.diff
session.error
session.idle
session.status
tool.execute.before
tool.execute.after
```

and more. ([OpenCode][6])

That is extremely valuable for Symphysis.

You could theoretically implement:

```typescript
SymphysisPlugin
    ↓
tool.execute.before
    ↓
lookup Agent Passport
    ↓
evaluate capability
    ↓
allow / modify / reject
```

and:

```typescript
tool.execute.after
    ↓
serialize event
    ↓
POST /events
    ↓
Symphysis audit store
```

OpenCode also allows custom tools, structured logging, environment manipulation, compaction hooks, etc. ([OpenCode][6])

### Its agent model is also very close to yours

OpenCode has primary agents and subagents, and subagents execute in child sessions. The `task` permission controls which subagents a parent can launch. ([OpenCode][7])

It also supports per-agent tool permissions and granular command/path matching. ([OpenCode][8])

That maps nicely to an Agent Passport.

For example, your passport could express:

```json
{
  "agent_id": "researcher-01",
  "capabilities": [
    "read:knowledge/*",
    "web:search",
    "spawn:reviewer"
  ],
  "denied": [
    "write:*",
    "shell:*",
    "credentials:*"
  ],
  "budget": {
    "tokens": 500000,
    "children": 4,
    "wall_time": 1800
  }
}
```

and Symphysis translates that into OpenCode permissions.

### The serious weakness

There is one architectural issue I would pay very close attention to.

OpenCode's child agents use **their own permissions**, rather than inheriting a restricted subset of the parent's permissions. ([OpenCode][9])

That is perfectly reasonable for a developer-oriented coding agent.

It is **not sufficient as your authoritative security model**.

Therefore:

> **Do not make OpenCode's permission configuration the source of truth for Agent Passport governance.**

Symphysis needs to remain above it.

---

# 4. Claw Code Agent

There are several unrelated projects called ClawCode, so this needs qualification.

The one that is especially relevant to you is **HarnessLab/claw-code-agent**.

This is interesting because it is explicitly a Python reimplementation of the Claude Code agent architecture, designed for local models and full control. ([GitHub][10])

And its feature list is almost suspiciously close to your requirements:

* nested agent delegation
* agent lineage tracking
* agent manager
* plugin runtime
* tool blocking
* cost budgets
* model-call limits
* tool-call limits
* session-turn limits
* structured outputs
* context compaction
* file-history journaling
* policy runtime
* MCP
* background sessions
* agent teams
* task orchestration
* event counters
* orchestration reports

([GitHub][10])

This is the project I would study very closely.

It is particularly interesting because your package is Python.

You could potentially take ideas from its architecture without introducing a TS/Bun runtime into Symphysis.

### Claw Code's biggest advantage for Symphysis

The conceptual model:

```text
Agent
 ├── identity
 ├── permissions
 ├── tools
 ├── budget
 ├── session
 ├── children
 └── lineage
```

is already much closer to your vision than a normal coding assistant.

### But there is a catch

It is a relatively small project compared with OpenCode. The repository currently reports roughly 226 forks, 8 issues and 6 PRs, whereas OpenCode is orders of magnitude larger, with roughly 190k GitHub stars and 24k forks at the time I checked. ([GitHub][10])

So I would treat Claw Code Agent as:

> **excellent architectural inspiration, potentially useful code, but not yet the foundation I would entrust with Symphysis's long-term runtime.**

---

# 5. OpenMonoAgent

OpenMono is different.

Its core philosophy is:

> local-first, zero cloud, bundled inference, Docker sandboxing.

It combines a .NET 10 CLI with llama.cpp and provides 20 tools plus an agentic pipeline. ([GitHub][11])

It actually has quite an interesting internal execution pipeline:

```text
parse
 → schema validate
 → path sanity
 → plan-mode guard
 → capability check
 → cache
 → pre-hook
 → execute
 → post-hook
 → artifact store
```

That is a very nice pattern for Symphysis. ([GitHub][11])

It also has several specialist subagents:

```text
Explore
Plan
Coder
Verify
```

with different tool sets and turn budgets. ([GitHub][11])

And it has playbooks, checkpoints, distributed inference, MCP integrations and ACP support. ([GitHub][11])

### Why I wouldn't choose it as Symphysis's core

Its center of gravity is:

```text
local coding assistant
        +
bundled local inference
        +
developer experience
```

Where Symphysis needs:

```text
agent governance
        +
portable identity
        +
delegation
        +
policy
        +
audit
        +
provider independence
        +
research workloads
```

OpenMono is also AGPL-3.0 licensed. ([GitHub][12])

That does not make it bad. It just makes it considerably less attractive as a base for something you may eventually want to distribute as a broadly reusable Python library.

---

# 6. The comparison for Symphysis

Here is how I would score them specifically against **your** objective.

| Capability                       | Claude Code | OpenCode | Claw Code Agent | OpenMono |
| -------------------------------- | ----------: | -------: | --------------: | -------: |
| Agent quality                    |      **10** |        9 |               7 |        7 |
| Harness maturity                 |      **10** |   **10** |               6 |        6 |
| Open source                      |           ❌ |   **10** |          **10** |   **10** |
| Provider independence            |           3 |   **10** |          **10** |        7 |
| Local models                     |           4 |   **10** |          **10** |   **10** |
| Agent spawning                   |      **10** |    **9** |          **10** |        8 |
| Agent lineage                    |           9 |        8 |          **10** |        7 |
| Tool interception                |      **10** |   **10** |               9 |    **9** |
| Policy enforcement               |      **10** |        8 |           **9** |        9 |
| Python integration               |           6 |        5 |          **10** |        3 |
| MCP                              |      **10** |   **10** |          **10** |        8 |
| Structured event stream          |      **10** |    **9** |           **9** |        8 |
| Long-term ecosystem              |      **10** |   **10** |               5 |        5 |
| Suitable as Symphysis foundation |           5 |    **9** |               8 |        6 |

The two biggest rows for you are actually:

**Python integration** and **policy/control-plane separation**.

---

# 7. The thing I would change in Symphysis

I would actually **avoid making "agent" equal to "LLM conversation."**

Define an agent as an identity + capabilities + runtime.

Something like:

```python
class AgentPassport:
    agent_id: str
    did: str
    issuer: str
    role: str

    runtime: RuntimeSpec
    model: ModelSpec

    capabilities: CapabilitySet
    policies: PolicySet

    resources: ResourceLimits
    parent: AgentRef | None

    delegation: DelegationPolicy
    audit: AuditPolicy
```

Then:

```python
agent = symphysis.spawn(passport)
```

does **not** mean:

```python
create_llm_client()
```

It means:

```text
verify passport
        ↓
verify issuer / credential
        ↓
establish identity
        ↓
derive capabilities
        ↓
allocate budget
        ↓
create isolated execution environment
        ↓
start runtime
        ↓
attach event sink
        ↓
start agent
```

That is much more powerful.

---

# 8. Your Agent Passport becomes the really interesting part

I would make the passport the cryptographic authority.

For example:

```json
{
  "version": "1.0",

  "identity": {
    "did": "did:key:z6Mk...",
    "agent_id": "researcher:security:001"
  },

  "issuer": {
    "did": "did:key:z6Mk..."
  },

  "runtime": {
    "type": "opencode",
    "version": ">=1.4"
  },

  "model": {
    "provider": "anthropic",
    "model": "claude-sonnet"
  },

  "capabilities": {
    "filesystem": [
      "knowledge/**"
    ],
    "network": [
      "https://arxiv.org/**"
    ],
    "tools": [
      "search",
      "read_file"
    ],
    "delegation": [
      "reviewer"
    ]
  },

  "limits": {
    "max_children": 3,
    "max_depth": 2,
    "max_tokens": 250000,
    "max_tool_calls": 500,
    "max_runtime_seconds": 1800
  },

  "policy": {
    "shell": "deny",
    "write": "deny",
    "credentials": "deny"
  }
}
```

Then the harness is merely the **execution engine**.

---

# 9. Agent spawning becomes really interesting

Instead of:

```text
Agent A → Agent tool → Agent B
```

I would make Symphysis own the operation:

```text
Agent A
   │
   │ "spawn reviewer"
   ▼
Symphysis Spawn Authority
   │
   ├─ verify A's passport
   ├─ verify A can delegate
   ├─ create child identity
   ├─ derive child capabilities
   ├─ allocate child budget
   ├─ establish lineage
   ├─ create sandbox
   ├─ start runtime
   └─ issue child passport
              │
              ▼
          Agent B
```

This gives you:

```text
Root Agent
│
├── Research Agent
│   ├── Literature Agent
│   └── Evidence Agent
│
├── Analyst Agent
│   ├── Statistical Agent
│   └── Critic Agent
│
└── Reviewer Agent
```

with an actual cryptographic lineage:

```text
root.did
  └── child.did
        └── child.did
```

That is significantly more interesting than simply supporting Claude-style subagents.

---

# 10. Logging "everything"

This needs one important distinction.

I would **not make raw hidden chain-of-thought a requirement**.

The model may not expose it, providers differ in how reasoning is represented, and treating private reasoning as the canonical audit trail makes your architecture provider-dependent.

Instead, make **agent execution events** the canonical audit primitive.

For example:

```json
{
  "event": "tool.requested",
  "timestamp": "...",

  "run_id": "...",
  "agent_id": "...",
  "parent_agent_id": "...",

  "tool": "web_search",

  "arguments": {
    "query": "..."
  },

  "policy": {
    "decision": "allow",
    "policy_id": "passport-policy-v3"
  }
}
```

Then:

```text
agent.created
agent.spawn_requested
agent.spawn_approved
agent.spawn_denied

model.requested
model.response

reasoning.summary

tool.requested
tool.authorized
tool.denied
tool.started
tool.completed
tool.failed

file.read
file.write
shell.executed
network.request

context.compacted

budget.warning
budget.exceeded

agent.completed
agent.failed
agent.terminated
```

You can optionally retain:

```text
reasoning.raw
```

when the specific model/API exposes a legitimate reasoning representation.

That makes Symphysis **far more portable**.

---

# 11. This gives you another important advantage

You can run:

```text
Claude
GPT
Qwen
Mistral
DeepSeek
Gemma
local models
```

under the same governance system.

The model becomes almost incidental:

```text
Agent Passport
      │
      ├── model = Claude
      │
      ├── model = Qwen
      │
      └── model = local vLLM
```

The **identity and authority remain constant**.

That is exactly the direction your current Symphysis design is already heading toward. ([PyPI][1])

---

# 12. What I would actually build

I would build Symphysis around five layers:

### `symphysis-core`

Pure Python abstractions:

```text
Agent
AgentPassport
AgentIdentity
Capability
Policy
Credential
Run
Event
Budget
Lineage
```

### `symphysis-policy`

A real authorization engine:

```python
decision = policy.evaluate(
    agent=agent,
    action=action,
    resource=resource,
    context=context
)
```

Eventually this could move toward something Cedar/OPA-like. Your current Symphysis implementation itself describes the existing permission mechanism as glob/allowlist enforcement rather than a general policy engine. ([PyPI][1])

### `symphysis-runtime`

Adapters:

```text
OpenCodeRuntime
ClaudeCodeRuntime
ClawCodeRuntime
OllamaRuntime
CustomRuntime
```

with a common interface:

```python
runtime.spawn(...)
runtime.send(...)
runtime.cancel(...)
runtime.events()
runtime.shutdown()
```

### `symphysis-audit`

An append-only event system:

```text
JSONL
SQLite
Postgres
OpenTelemetry
Kafka
```

depending on deployment.

### `symphysis-sandbox`

Actual enforcement.

This is critical.

Do **not** rely solely on:

```text
LLM instructions
+
prompt
+
permissions JSON
```

for serious governance.

Use:

```text
container
seccomp
filesystem mounts
network policy
credential broker
resource quotas
process limits
```

where necessary.

That is the difference between:

> "the agent was told not to do something"

and:

> "the agent was technically incapable of doing something."

---

# 13. Where OpenCode fits

I would make OpenCode the first external runtime adapter.

Something like:

```text
Symphysis
   │
   │ spawn(passport)
   ▼
OpenCode adapter
   │
   ├── creates OpenCode session
   ├── loads derived agent configuration
   ├── configures tools
   ├── configures permissions
   ├── attaches event hooks
   └── streams events back
          │
          ▼
   Symphysis Event Bus
```

OpenCode already has a server/client architecture and a TypeScript SDK, so there is a reasonable separation between your Python control plane and the execution runtime. ([OpenCode][13])

It also supports ACP, which may eventually give you another clean agent/runtime boundary. ACP allows OpenCode to run as a subprocess and communicate over JSON-RPC/stdin/stdout. ([OpenCode][14])

---

# 14. Where Claw Code fits

I would use Claw Code Agent almost as a **reference implementation for Symphysis ideas**.

Especially study its:

```text
Agent Manager
Lineage
Nested Delegation
Budget system
Policy runtime
Background sessions
Workflow runtime
Event counters
```

Those ideas are unusually aligned with Symphysis. ([GitHub][10])

Because it is Python, concepts can likely be translated into Symphysis far more easily than OpenCode's TypeScript architecture.

---

# 15. What I would not do

I would **not** fork OpenCode and rename it Symphysis.

I would **not** fork Claude Code.

I would **not** put the Agent Passport inside a specific coding agent.

And I would **not** make the runtime responsible for authoritative authorization.

Instead:

```text
              SYMPHYSIS
          identity + policy
         spawn + audit + trust
                  │
        ┌─────────┼─────────┐
        │         │         │
     OpenCode  ClawCode  Custom
        │         │         │
        └─────────┼─────────┘
                  │
                LLMs
```

That makes Symphysis a **portable agent governance layer**, rather than another Claude Code clone.

---

# My recommendation

Given what Symphysis already contains, I would pursue this stack:

**Symphysis = control plane**

**OpenCode = first high-quality execution backend**

**Claw Code Agent = Python reference implementation / source of architectural ideas**

**OpenMono = local-first runtime to study later**

**Claude Code = gold-standard behavioral benchmark**

The most valuable thing you can build is not another coding agent.

It is this:

> **A portable, cryptographically identifiable, policy-constrained, auditable agent runtime where agents can spawn other agents without escaping the authority that created them.**

That is a much stronger project than "open-source Claude Code."

And your existing Agent Card/DID architecture is already unusually well positioned for it. ([PyPI][1])

One caveat: the name **Claw Code** currently refers to multiple unrelated repositories. I based the substantive Python comparison on `HarnessLab/claw-code-agent`, because its architecture most directly matches your Symphysis use case. There is also a separate Rust `StartripAI/claw_code`, which claims Claude Code parity but is currently a very small repository, so I would not weight it heavily in the architectural decision. ([GitHub][15])

[1]: https://pypi.org/project/symphysis/?utm_source=chatgpt.com "symphysis · PyPI"
[2]: https://code.claude.com/docs/en/agent-sdk/claude-code-features?utm_source=chatgpt.com "Use Claude Code features in the SDK - Claude Code Docs"
[3]: https://code.claude.com/docs/en/agent-sdk/hooks?utm_source=chatgpt.com "Intercept and control agent behavior with hooks - Claude Code Docs"
[4]: https://github.com/anthropics/claude-code/blob/main/LICENSE.md?utm_source=chatgpt.com "claude-code/LICENSE.md at main · anthropics/claude-code · GitHub"
[5]: https://github.com/anomalyco/opencode/?utm_source=chatgpt.com "GitHub - anomalyco/opencode: The open source coding agent. · GitHub"
[6]: https://opencode.ai/docs/plugins/ "Plugins | OpenCode"
[7]: https://opencode.ai/v2/docs/agents "Agents | OpenCode"
[8]: https://opencode.ai/docs/agents/?utm_source=chatgpt.com "Agents | OpenCode"
[9]: https://opencode.ai/v2/docs/agents?utm_source=chatgpt.com "Agents | OpenCode"
[10]: https://github.com/HarnessLab/claw-code-agent/blob/main/README.md "claw-code-agent/README.md at main · HarnessLab/claw-code-agent · GitHub"
[11]: https://github.com/StartupHakk/OpenMonoAgent.ai "GitHub - StartupHakk/OpenMonoAgent.ai: (BETA) AI shouldn't have a meter. Unlimited tokens. Forever. Your machine. Your agent. Use it from anywhere. Terminal-native coding agent powered by local LLMs — 100% open source, free forever, and installed with a single command. Proudly built on C#/.NET, because AI tooling should be infrastructure, not a subscription. · GitHub"
[12]: https://github.com/StartupHakk/OpenMonoAgent.ai/blob/main/LICENSE?utm_source=chatgpt.com "OpenMonoAgent.ai/LICENSE at main · StartupHakk/OpenMonoAgent.ai · GitHub"
[13]: https://opencode.ai/docs/es/sdk/?utm_source=chatgpt.com "SDK | OpenCode"
[14]: https://dev.opencode.ai/docs/acp/?utm_source=chatgpt.com "ACP Support | OpenCode"
[15]: https://github.com/StartripAI/claw_code "GitHub - StartripAI/claw_code: 🦀 Production-grade Rust rewrite of Claude Code. 42 native tools, multi-provider, 100% parity. · GitHub"

