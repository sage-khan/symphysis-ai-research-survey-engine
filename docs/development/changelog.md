# Changelog

All notable changes to agentic-survey-tool. Bug fixes and their root causes
are tracked separately in `diagnostics.md`.

## 2026-08-02

- Full trace and consolidated output per agent: every provider's exact
  outgoing prompt is now logged (`prompt.md`), RAG retrieval is logged as a
  discrete tool-call event in `conversation.jsonl`, and each agent gets a
  single human-readable `filled_survey.md` (role/model/DID/RAG header,
  Best/Worst summary table, full comparison tables and reasoning per
  sample) instead of needing `samples/*.json` and `conversation.jsonl` open
  side by side.
- Confirmed remote-LLM mode: the app can run entirely on a local machine
  while calling the veritas server's Ollama instance over Tailscale
  (`OLLAMA_BASE_URL=http://<tailscale-ip>:11434`); the Bayesian solve stays
  local and fast regardless of where the LLM calls go.
- Copied and curated VERITAS's project-wide `.claude/rules/` into this repo
  (gitops, file-read-write, software-directory-structure-guide,
  writing-style, aboutme), dropping the paper/literature-specific rules
  that don't apply to a software tool repo, and wrote this project's own
  `project-details.md`.

## 2026-08-02 (earlier)

- Agent Card redesign: agents are now spawned from a single portable JSON
  file (DID, role, model, RAG, sampling, permissions, guardrails,
  environment) instead of split YAML config + a runtime-generated DID.
  Real `did:key` identity (Ed25519, W3C Verifiable Credentials), ported from
  project-cogtwins's verified `identity.py` pattern.
- Added a `manual` provider for models with no API (Gemini/GPT web chat):
  writes the exact prompt to paste, waits for the pasted reply, resumes
  across process restarts without re-asking answered samples.
- Permissions (`data_scopes`, `allowed_providers`) enforced, not just
  documented.
- Migrated the example `bsi-hawc-bwm` survey's roster to 17 agents: 6
  domain-persona roles (BIM coordinator, compliance officer, structural
  engineer, project manager, blockchain engineer, data engineer) each bound
  to one of 6 diverse Ollama model families (Qwen, Gemma, Llama, Mistral,
  DeepSeek, Phi), plus a 5-agent "independent reviewer" cross-check tier
  (Claude Opus/Sonnet/Haiku, manual Gemini/GPT).
- Live end-to-end validation on the veritas server (real LLM calls, not
  mocked) surfaced and fixed three real bugs; see `diagnostics.md`.

## 2026-08-01

- Initial release: config-driven agents (YAML at this point), provider
  abstraction (Ollama/Anthropic/OpenAI/OpenRouter), BWM instrument,
  guardrails (schema validation, retry, repeated sampling), classical and
  Bayesian BWM solvers ported from `bsi-survey-app` and verified against the
  original authors' reference implementations, Docker deployment, initial
  `bsi-hawc-bwm` example survey.
