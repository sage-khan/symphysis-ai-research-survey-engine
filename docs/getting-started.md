# Getting started

Two walkthroughs: a minimal survey run entirely from the command line with
no external accounts (a manual-provider agent, so there is nothing to
install or authenticate), and the same survey run against a real local
model via Ollama. Both produce a real, solved Best-Worst Method report,
not a demo stub. A third section covers the web UI, which is how most of
this repository's own example surveys were actually authored and run.

## Walkthrough 1: a minimal survey, zero setup

Two ways to get the same `survey.yaml` + agent card on disk: the
`symphysis` CLI (fastest), or hand-authoring the two files directly (shown
below, useful for understanding the actual format the CLI generates).

**The fast way**, once `symphysis` is installed (`pip install symphysis`,
or `pip install -e .` from a checkout of this repo):

```bash
symphysis new getting-started-demo --dimensions LATENCY,COST,ACCURACY --output surveys/getting-started-demo
symphysis add-agent surveys/getting-started-demo \
  --agent-id reviewer-one --role "Site Reliability Engineer" \
  --provider manual --model claude-opus-5
symphysis fix-survey surveys/getting-started-demo   # sanity-check before running
```

This produces the same `survey.yaml` and `agents/reviewer-one.json` shown
below (edit `role_description` and `instrument_params.dimension_labels`
afterward for the same result), then skip ahead to "Run it."

**The hand-authored way**, for the same result without the CLI:

```bash
mkdir -p surveys/getting-started-demo/agents
```

`surveys/getting-started-demo/survey.yaml`:

```yaml
id: getting-started-demo
title: "Getting started: which failure mode matters most?"
instrument: bwm
instrument_params:
  dimensions: [LATENCY, COST, ACCURACY]
  dimension_labels:
    LATENCY: How slow the system gets under load
    COST: How much it costs to run
    ACCURACY: How often it gives the wrong answer
```

`surveys/getting-started-demo/agents/reviewer-one.json` (a real Agent
Card; `did_seed` and the `did` block below make its identity
reproducible, see "The Agent Card" in the README for what every field
means):

```json
{
  "schema_version": "1.0",
  "agent_id": "reviewer-one",
  "role": "Site Reliability Engineer",
  "role_description": "An SRE who has been paged for all three failure modes in production.",
  "instrument": "bwm",
  "system_prompt_template": "config/prompts/expert_panel_system.txt",
  "model": {"provider": "manual", "name": "claude-opus-5", "temperature": 0.7, "max_tokens": 1024, "top_p": 1.0, "seed": 42},
  "rag": {"enabled": false, "corpus_path": null, "top_k": 5, "embedding_model": "sentence-transformers/all-MiniLM-L6-v2", "chunk_size": 800, "chunk_overlap": 100},
  "sampling": {"repeats": 1, "max_retries_on_malformed": 2, "agreement_threshold": 0.0},
  "permissions": {"data_scopes": [], "network": [], "allowed_providers": ["manual"], "max_cost_usd": null},
  "guardrails": {"schema_validation": true, "denylist_patterns": ["ignore (all|any|the) (previous|prior|above) instructions"]},
  "did": {"method": "did:key", "id": "did:key:z6Mkf5rGMhcVXX8XvBWfxwbdxLnwqYE1DKJnpi9GkyKtRK4E", "public_key_multibase": "z6Mkf5rGMhcVXX8XvBWfxwbdxLnwqYE1DKJnpi9GkyKtRK4E", "deterministic": true, "seed_derivation": "sha256('getting-started-demo:reviewer-one')"},
  "environment": {"runtime": "symphysis", "runtime_version": "0.1.0", "python_version": "3.11", "platform": "generic", "container_image": null}
}
```

Run it:

```bash
PYTHONPATH=src python -m symphysis.cli run surveys/getting-started-demo
```

Since `model.provider` is `manual`, the run stops with a message pointing
at `surveys/getting-started-demo/agents/reviewer-one/manual_input/prompt_00.md`.
Open that file, paste its contents into any chat model's UI, and save the
reply to the matching `response_00.txt` in the same directory. Re-run the
exact command above. This time it completes and writes
`surveys/getting-started-demo/report/report.md` with the solved weights,
plus `report/charts/*.png`.

## Walkthrough 2: the same survey, a real local model

Install and start [Ollama](https://ollama.com), pull any model
(`ollama pull llama3.1:8b`), then change `reviewer-one.json`'s `model`
block to:

```json
"model": {"provider": "ollama", "name": "llama3.1:8b", "temperature": 0.7, "max_tokens": 1536, "top_p": 1.0, "seed": 42}
```

and its `permissions.allowed_providers` to `["ollama"]`. Delete the
`surveys/getting-started-demo/agents/reviewer-one/` runtime folder if the
manual walkthrough above already created one (a fresh agent identity
folder is created on the next run), then re-run the same CLI command.
`symphysis run` checks Ollama's reachable with that model pulled as its
very first step, printed before anything else; if that check fails, fix
Ollama first rather than waiting to see the same failure deeper into the
run. Once it passes: no `manual_input` step this time; the agent calls
Ollama directly and the report is written in one pass. If a level's response gets cut off or
rejected by the guardrails, see the "Hierarchical BWM" section of the
README and `docs/development/diagnostics.md` for the two most common
causes (an undersized `max_tokens` for the task, and a model that
misreads the Best-Worst self-comparison convention), both real issues hit
and fixed during this project's own development.

## Walkthrough 3: the web UI, and linking a knowledge base

The web UI (`web/backend`, `web/frontend`, see "Setup" in the README to
start both) is how to create a survey through a form instead of hand
editing YAML, add agents from the reusable Agent Library instead of
writing a new JSON file every time, and watch a run's live progress.

1. **Surveys -> New survey**: describe the survey in plain language or
   upload a document; the concept-driven proposer drafts a title,
   description, and dimension list for review before anything is created.
2. **Agent Library -> Knowledge Bases tab -> New knowledge base**: give it
   an id and a name, then **Upload file** to add real reference material
   (`.md`/`.txt` directly, `.pdf`/`.docx` converted to `.md` on upload).
   This is the reusable alternative to giving every agent its own,
   one-off corpus.
3. **Agent Library -> Agents tab -> + New agent**, or a survey's own Agents
   tab: fill in role, model, and check "RAG-augmented"; the knowledge base
   created in step 2 now appears in a dropdown, and selecting it sets
   that agent's corpus path (and the matching permission scope) to the
   same directory, no re-upload needed.
4. **Run survey**: while it runs, the page shows a live progress panel
   (percentage of agents attempted, a status chip per agent) rather than
   only a spinner.
5. **Results / Analytics tabs**: the solved report and charts once
   complete, and, at any point, a full accounting of who contributed,
   who didn't, and why, derived entirely from what's actually on disk
   (see "Analytics: who said what" in the README).

## Where to go next

- The README's "How it works" section for the full request/response
  pipeline underneath both walkthroughs above.
- "The Agent Card" section for what every field in `reviewer-one.json`
  actually means and why identity is separated from configuration.
- "Hierarchical BWM" for multi-level criteria trees (TrustRouter/BSI's own
  real use case, in `surveys/bsi-hawc-bwm/`, is the fully worked example).
- `/docs` on a running backend for the interactive API reference (see
  "API documentation" in the README).
