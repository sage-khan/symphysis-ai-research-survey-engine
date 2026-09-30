# Result provenance and watermarking: architecture plan

**Status:** Plan only. Nothing in this document is implemented yet, as of
2026-09-06. Companion to `governance-layer-and-runtime-backends-plan.md`:
that plan built the identity/spawning/capability substrate this plan
reuses (`identity/did.py`, `identity/credentials.py`) and the tamper-
evidence baseline this plan extends (`integrity.py`). Read those first.

## 1. What this is

Two related but distinct goals, asked for together, kept separate here
because they have very different feasibility:

1. **Watermarking:** a way to tell, from the text of a response alone,
   that it genuinely came from a real model completion, not from a human
   typing it and pasting it in as if a model produced it.
2. **Verification:** a way for anyone (Dan, a reviewer, a reader of a
   published paper citing this tool's results) to check that a given
   survey's stored results genuinely came from this tool's own pipeline,
   and that nothing was deliberately altered after the fact.

Both serve the same standing rule this project already states in its own
root `CLAUDE.md`: results from this tool must never be fabricated or
silently substituted, and any run must plainly disclose what actually
happened. Today that rule is enforced procedurally (Dan's own discipline,
and this app's guardrails/skip-and-report behavior) plus `integrity.py`'s
SHA-256 manifest, which detects file changes from the moment a run
finishes onward. This plan closes the gap before that point: was the
stored text ever genuinely produced by the claimed model in the first
place, and can that be checked independently of trusting this app's own
code at the time it ran.

## 2. Threat model

What this plan defends against:

- A stored sample being edited after it was written (already partly
  covered by `integrity.py`; Layer 1 below extends the same guarantee
  down to the moment of generation, not just the moment a run finishes).
- Someone claiming a response came from model X when it was actually
  hand-authored, copy-pasted from a different model, or edited before
  being accepted, in a way that is checkable without re-running the
  survey or trusting whoever is presenting the result.
- A dispute, months or years after a run, over whether a specific number
  in a published paper actually traces back to a real completion.

What this plan does not, and cannot, defend against:

- Someone who controls the entire pipeline (this app's own code, the
  machine it runs on, and the signing keys) at the moment a survey runs.
  Cryptographic signing proves "the holder of this key attests to this
  text at this time"; it cannot prove the holder of the key told the
  truth about where the text came from. Defending against a fully
  malicious operator requires a remote-attestation or trusted-third-party
  scheme (an external, independently-operated verifier signs or witnesses
  the completion), which is out of scope for this plan and listed as an
  open question in section 6.
- A watermark surviving arbitrary paraphrase, translation, or heavy
  editing of the text after generation. Every published watermarking
  scheme degrades under enough post-generation transformation; this plan
  is aimed at detecting "was this exact text ever a real completion," not
  at surviving deliberate adversarial rewriting.

## 3. Design principles (binding on both layers)

- **No half-built claims.** If a check cannot be made honestly, this
  project's own report and CLI output must say so plainly (`"not
  verifiable: no attestation recorded"`), never present an unverified
  result as verified. This is the same rule `integrity.py`'s own
  `VerificationResult.ok` already applies: an honest, unqualified
  verification, never partial credit.
- **Reuse the existing cryptographic substrate.** `identity/did.py`
  (Ed25519 `did:key`) and `identity/credentials.py`
  (`issue_credential`/`verify_credential`) already do real signing and
  verification for spawn declarations; Layer 1 is the same primitive
  applied to one more claim type, not a new cryptographic scheme.
- **Verifiable without this app installed.** `integrity.py`'s own stated
  goal (a reviewer checks with `sha256sum -c`, no copy of this
  application required) extends to Layer 1: verifying an attestation
  signature needs only the stored public DID and a standard Ed25519
  library, not a running Symphysis instance.
- **Local-first stays honestly scoped.** Watermarking Ollama-served
  open-weight models is, in principle, fully within this project's own
  control (no third party to depend on); watermarking a hosted provider's
  output is not, and this plan must not claim a capability for a hosted
  provider that provider does not itself support.

## 4. Layer 1: generation-time provenance attestation (buildable now)

The moment a `ProviderResponse` is received, before anything else touches
it, sign a claim binding together: the calling agent's DID, the exact
outgoing prompt (hashed, not embedded in full, to keep the attestation
small), the exact raw response text (hashed), the model/provider name, and
a timestamp. This is not a text watermark (it does not survive the text
being copied out of this app's own storage into, say, a paper's block
quote); it is a signed record that "this agent attests that this exact
prompt-response pair was produced at this time," verifiable independently
of trusting this app's code at read time.

### Concrete tasks

1. `identity/credentials.py`: add a `"CompletionAttestation"` claim type
   (reusing `issue_credential`/`verify_credential` unchanged; only a new
   `credentialSubject` shape: `{"promptHash": ..., "responseHash": ...,
   "provider": ..., "model": ..., "sampleIndex": ...}`).
2. `guardrails.py::run_with_guardrails`: for every `ProviderResponse`
   received (accepted or rejected; a rejected sample is exactly as
   important to attest, since a dispute might be about why something was
   rejected), compute `sha256(json.dumps(attempt_messages))` and
   `sha256(response.text)`, and have the calling agent's identity sign a
   `CompletionAttestation` over them. Requires threading the agent's
   `AgentIdentity` (not just its `AgentCard`) into `run_with_guardrails`;
   today only `spawning/spawn.py` holds a live `AgentIdentity`, so this
   also means `Agent` gains a way to rehydrate or hold its own signing
   identity for the duration of a run (see `agent_card.py::rehydrate_identity`,
   already built for a deterministic card, currently only used by CLI
   tooling, not by a live run).
3. `audit/logger.py`: `write_completion_attestation(agent_id, sample_index,
   attestation)`, alongside each `samples/sample_N.json`, following the
   existing per-sample file convention.
4. `integrity.py` (or a new sibling module, `provenance.py`, to keep
   `integrity.py` focused on its existing file-hash job): a
   `verify_attestations(survey_dir)` function that, for every stored
   sample, re-hashes its own `prompt.md`/`sample_N.json` content, checks
   the hash matches what the attestation claims, and verifies the
   attestation's signature against its stated agent DID's public key
   (already resolvable from `card.json`/`did.json`, no external key
   lookup needed). Reports per-sample: attested and matches, attested but
   hash mismatch (the strongest possible tamper signal: a signed claim
   that no longer matches the file it was signed over), or not attested
   (every sample from before this feature existed, or a manual-provider
   sample with no automated completion to attest).
5. CLI: extend `fix_survey`/the existing `verify`-style command (or add
   `symphysis verify-provenance <survey>`) to run this check and print a
   plain report, same style as today's integrity verify output.
6. Web UI: surface per-sample attestation status alongside the existing
   integrity manifest check on the Results tab, not a new page.

This layer is real engineering, not a research problem: every primitive
it needs already exists and is tested (`identity/credentials.py`). Sized
similarly to the pipeline-stages work already landed.

## 5. Layer 2: statistical text watermarking (research-gated)

This is a substantially harder, and provider-dependent, problem. Stated
honestly rather than scoped down to look easier than it is:

- **Local/open-weight models via Ollama:** a real statistical watermark
  (for example, the green-list/red-list token-biasing scheme from
  Kirchenbauer et al. 2023) requires biasing the sampler's logits at
  every generation step, keyed by a rolling hash of prior tokens. Ollama's
  HTTP API does not expose this level of control; implementing it
  correctly means driving the underlying model directly (llama.cpp's own
  API, or a Python inference stack such as `transformers`/`vLLM` with a
  custom `LogitsProcessor`), bypassing Ollama entirely for any card that
  opts into watermarking. This is a genuine engineering project (a new,
  separate local-inference path, a detector that recomputes the same
  rolling hash over any given text and tests for the expected green-list
  bias), not a small addition, and changes this project's local-model
  story (today: point at any Ollama-served model; with this: a narrower
  set of models this app can drive directly).
- **Hosted providers (Anthropic, OpenAI, OpenRouter, Groq, Gemini, xAI):**
  Symphysis has no access to these providers' sampling process, so a
  provider-side watermark can only be used if the provider itself applies
  one and exposes a public detector. This must be checked per provider,
  not assumed; a provider offering this today does not guarantee it
  stays available, versioned, or free. If none of a survey's configured
  providers expose this, Layer 2 is simply unavailable for that survey,
  and this app's own output must say so plainly rather than implying
  watermark coverage it cannot actually provide.

### Recommended next step for Layer 2, not a build task yet

A short, time-boxed research spike: for each hosted provider this project
currently supports, check whether it documents a public watermark and
detector API as of the time of the check (a fact that can change, so this
check should be repeated before any Layer 2 work starts, not assumed from
this document). For the local path, prototype the llama.cpp/`transformers`
green-list scheme against one small model, offline, to get a real cost
estimate (latency overhead, detector false-positive rate) before deciding
whether it is worth the narrower local-model story it implies.

## 6. Open questions to resolve before Phase B (Layer 2) starts

- Is Layer 1 alone (signed generation-time attestation, verifiable
  independently of this app) sufficient for Dan's actual use case
  (defending a published paper's results against a dispute), or is
  survivable-in-isolation text watermarking (Layer 2) genuinely needed on
  top of it? These answer different questions: Layer 1 proves "this
  stored file was signed as a real completion at generation time," Layer
  2 would prove "this exact quoted sentence, seen anywhere, came from a
  real completion," which is a stronger and harder property.
- Does any currently-configured provider (see `providers/`) already
  publish a watermark/detector API worth wiring into Layer 1 as an
  additional, provider-native signal, rather than this project building
  its own for that provider.
- Should a fully independent, third-party attestation step (an external
  timestamping or witnessing service) be added on top of Layer 1, to
  close the "operator controls the whole pipeline" gap named in section
  2. Out of scope for this plan; recorded here so it is not silently
  forgotten.

## 7. What this plan deliberately does not do

- It does not claim watermark coverage for a provider that does not
  itself support it.
- It does not attempt to make a fabricated result indistinguishable from
  a genuine one detectable after arbitrary paraphrase or translation;
  see the threat model in section 2.
- It does not replace `integrity.py`'s existing file-level manifest;
  Layer 1 is additive; the manifest still covers everything in the
  survey folder, attested or not.
- It does not start Layer 2 engineering before the research spike in
  section 5 reports back with real numbers, per this project's own
  "no half-hearted implementation" rule.
