"""Standalone driver script, executed as a subprocess under
vendor/openmanus/.venv's own Python interpreter (a fully isolated venv,
python3.12, OpenManus's own pinned dependency stack installed via
`uv pip install -r vendor/openmanus/requirements.txt`), never imported as a
module and never sharing an interpreter with the rest of Symphysis.

Why a subprocess rather than an in-process import: OpenManus's
requirements.txt pins pydantic~=2.10.6 and pulls in ~30 packages
(browsergym, playwright, docker, boto3, crawl4ai, ...), several version-
pinned. Symphysis's own test suite already runs pymc/pytensor for the
Bayesian BWM solver in the same conda environment; installing OpenManus's
pins there risked a real dependency conflict. This script is deliberately
the ONLY place that imports anything under vendor/openmanus/'s `app`
package, and it does so from a completely separate interpreter, so it
carries zero Symphysis imports itself — the boundary is the JSON contract
below, not a shared Python process.

Usage: <isolated venv python> _openmanus_driver.py <input.json>

Input JSON shape (written by runtime/openmanus.py::OpenManusBackend.spawn,
using the same to_llm_settings() mapping tested in
tests/test_runtime_openmanus.py):
{
  "config_name": "<agent DID, keys OpenManus's process-wide LLM singleton cache>",
  "llm_settings": {"model": ..., "base_url": ..., "api_key": ..., "max_tokens": ...,
                    "temperature": ..., "api_type": ..., "api_version": ...},
  "messages": [{"role": "user"|"assistant", "content": "..."}, ...],
  "max_steps": 15,
  "proxy_port": 54321,           # optional: tools/proxy.py's ToolProxyServer port, if any
  "available_tools": [           # optional: which tools/registry.py ToolSpecs to expose,
    {"name": "rag_retrieval",    # each one becomes a ProxyTool that calls back to
     "description": "...",      # http://127.0.0.1:<proxy_port>/tools/<name> — see ProxyTool below
     "parameters": {"type": "object", "properties": {...}, "required": [...]}}
  ],
  "flow": "survey_panel",        # optional (Phase 3): when present, _run() drives
                                  # SurveyPanelFlow instead of the plain ToolCallAgent
                                  # loop below — one InstrumentSubmit-gated agent per
                                  # level instead of one whole-response completion.
                                  # Requires "levels"/"level_messages" below and an
                                  # "instrument_submit" entry in "available_tools".
  "levels": [{"id": "L1", "dimensions": [...]}, ...],   # required when flow="survey_panel"
  "level_messages": {"L1": [{"role": ..., "content": ...}, ...], ...},  # required when flow="survey_panel"
  "level_max_steps": 5           # optional (Phase 3): per-level step budget, independent
                                  # of the top-level "max_steps" above (default 5)
  "flow": "bwm_two_stage",       # optional (2026-09-01): when present, _run() drives
                                  # _run_bwm_two_stage() instead of either flow above --
                                  # a flat (non-hierarchical) `bwm` instrument answered as
                                  # two plain, non-tool-calling completions (best/worst,
                                  # then dynamically-built ratings) instead of one
                                  # tool-calling turn. See agentic-experiment-design-
                                  # decisions.md (project-veritas) 2026-09-01 entries for
                                  # why: combining free-text reasoning with a structured
                                  # tool-call submission proved fragile for small local
                                  # models, and this flow was validated as the fix.
  "codes": ["DVS", "F", "E", "A"],          # required when flow="bwm_two_stage"
  "labels": {"DVS": "Data Value Score"},    # optional when flow="bwm_two_stage"
  "context_chunks": ["[role knowledge: ...] ...", "[rag: ...] ..."]  # optional when
                                             # flow="bwm_two_stage" -- RAG/knowledge-repo/
                                             # role-pack material (agent.py's Agent.run()
                                             # already assembled this the same way it does
                                             # for every other flow); prepended to turn 1's
                                             # prompt and kept in conversation history for
                                             # turn 2, exactly like any other flow's whole-
                                             # response prompt would carry it
}

Output: one JSON object per line on stdout (NDJSON), flushed immediately so
the parent process can stream events as they occur:
  {"kind": "thought"|"tool_call", "payload": {"step": N, "result": "..."}}
  {"kind": "raw_completion", "payload": {"response": {...}}}   # exactly one, last
  {"kind": "error", "payload": {"message": "..."}}             # only on failure
In flow="survey_panel" mode, every "thought"/"tool_call" payload also carries
a "level" key (the level id that step belongs to), and "raw_completion"'s
response.text is a JSON object shaped {"levels": {"L1": {...}, ...}} —
already the exact shape instrument.parse() (the outer, whole-response
validator) expects, since every level's answer it contains has already been
individually validated in-loop via instrument_submit before being included.
In flow="bwm_two_stage" mode, "thought" payloads carry "step": 1 (best/worst
elicitation) and "step": 2 (pairwise ratings), each with the raw model text
in "reasoning"; on success, "raw_completion"'s response.text is a JSON
object already shaped exactly as instruments/bwm.py::BWMInstrument.parse()
expects (best, worst, best_to_others, others_to_worst, reasoning) -- no
tool call is ever issued in this flow. On a turn 1/2 parse failure, this
flow still emits "raw_completion" (never "error"), but with a deliberately
incomplete JSON object (missing whatever field could not be determined) so
BWMInstrument.parse() flags it invalid and guardrails.py's existing
reject-and-repair loop retries it per-sample -- an "error" event here would
instead raise OpenManusProviderError, which orchestrator.py catches by
skipping the WHOLE agent, not just one malformed sample.

Exit code is 0 on a clean run (including one that ends in an "error" event
for an OpenManus-internal failure), nonzero only for a driver-level crash
before any output was produced (e.g. malformed input JSON).
"""

from __future__ import annotations

import asyncio
import json
import re
import sys
from pathlib import Path

_VENDOR_ROOT = Path(__file__).resolve().parents[3] / "vendor" / "openmanus"
sys.path.insert(0, str(_VENDOR_ROOT))


def _emit(kind: str, payload: dict) -> None:
    print(json.dumps({"kind": kind, "payload": payload}), flush=True)


def _build_proxy_tool_class():
    """A generic OpenManus BaseTool that bridges one tool call back to the
    parent Symphysis process's real tools/registry.py ToolSpec of the same
    name, via tools/proxy.py's local-only HTTP server (started by
    runtime/openmanus.py::OpenManusProvider before this subprocess is
    launched). This is the only way this script ever touches RAG
    retrieval, web search, or citation verification: none of that code is
    importable here (see module docstring)."""
    from app.tool.base import BaseTool, ToolResult

    class ProxyTool(BaseTool):
        proxy_port: int
        proxy_tool_name: str

        async def execute(self, **kwargs) -> ToolResult:
            import httpx

            url = f"http://127.0.0.1:{self.proxy_port}/tools/{self.proxy_tool_name}"
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(url, json=kwargs)
            except httpx.HTTPError as exc:
                return ToolResult(error=f"proxy call to {self.proxy_tool_name!r} failed: {exc}")

            if resp.status_code != 200:
                return ToolResult(
                    error=f"proxy call to {self.proxy_tool_name!r} returned {resp.status_code}: {resp.text}"
                )
            return ToolResult(output=json.dumps(resp.json()))

    return ProxyTool


def _build_instrument_submit_proxy_tool_class(ProxyTool):
    """Phase 3's InstrumentSubmit tool: a ProxyTool (see above) with extra
    bookkeeping SurveyPanelFlow (below) reads directly, not just what the
    LLM sees in its own transcript. The flow needs to know PROGRAMMATICALLY
    when a level's submission was accepted (to stop stepping that level)
    and what the last-attempted answer was (to fall back to if a level
    never converges within its step budget) — information the LLM's own
    tool-call transcript carries informally but this script cannot cheaply
    re-parse back out. Takes ProxyTool as a parameter rather than importing
    it itself so there is exactly one place (_run()) that decides whether
    this subclass or the plain ProxyTool wraps a given registered tool."""
    from pydantic import Field

    class InstrumentSubmitProxyTool(ProxyTool):
        accepted: dict = Field(default_factory=dict)       # level_id -> the answer dict that got valid=true
        last_attempt: dict = Field(default_factory=dict)   # level_id -> the most recent submission, valid or not

        async def execute(self, **kwargs):
            result = await super().execute(**kwargs)
            level_id = kwargs.get("level_id")
            if level_id is None:
                return result
            answer = {k: v for k, v in kwargs.items() if k != "level_id"}
            self.last_attempt[level_id] = answer
            if result.error is None and result.output:
                try:
                    parsed = json.loads(result.output)
                except (TypeError, ValueError):
                    parsed = None
                if parsed and parsed.get("valid"):
                    self.accepted[level_id] = answer
            return result

    return InstrumentSubmitProxyTool


def _build_survey_panel_flow_class():
    """Phase 3 (docs/architecture/governance-layer-and-runtime-backends-plan.md
    tasks 17-19): one level per plan step, gated on InstrumentSubmit
    accepting that level before the next one starts, so a model's per-level
    convention mistake costs one tool-call retry instead of a whole
    multi-level response's reject-and-repair round (see
    instruments/hierarchical_bwm.py's parse()/_validate_level_fields()
    comment on why whole-response retries converged poorly against a model
    with one systematic per-level mistake).

    A fresh agent instance is constructed per level (sharing the SAME llm
    and available_tools instances, so InstrumentSubmitProxyTool's
    accepted/last_attempt bookkeeping persists across levels) rather than
    resetting one long-lived agent's internal state between levels: this
    sidesteps needing to know OpenManus's exact ReAct-agent reset semantics
    (memory/state/step-counter) at this pinned commit, at the cost of
    reconstructing a cheap Python object once per level."""
    from app.flow.base import BaseFlow
    from app.schema import AgentState, Message
    from pydantic import Field

    class SurveyPanelFlow(BaseFlow):
        levels: list = Field(default_factory=list)
        level_messages: dict = Field(default_factory=dict)
        level_max_steps: int = 5

        class Config:
            arbitrary_types_allowed = True

        async def execute(self, input_text: str) -> str:
            agent_cls = type(self.primary_agent)
            submit_tool = self.primary_agent.available_tools.get_tool("instrument_submit")
            level_results: dict = {}

            for level in self.levels:
                level_id = level["id"]
                level_agent = agent_cls(
                    llm=self.primary_agent.llm,
                    available_tools=self.primary_agent.available_tools,
                    max_steps=self.level_max_steps,
                )
                for msg in self.level_messages.get(level_id, []):
                    role, content = msg.get("role", "user"), msg.get("content", "")
                    if role == "system":
                        continue
                    level_agent.memory.add_message(
                        Message.user_message(content) if role == "user" else Message.assistant_message(content)
                    )

                while level_agent.state != AgentState.FINISHED and level_agent.current_step < level_agent.max_steps:
                    pre_len = len(level_agent.memory.messages)
                    result = await level_agent.step()
                    level_agent.current_step += 1
                    # step() = think() (adds exactly one new assistant-role
                    # message carrying the model's own reasoning content,
                    # even on a turn that also issues a tool call) + act()
                    # (returns only the post-execution tool OBSERVATION,
                    # never the reasoning itself). Recover that content from
                    # memory so the persisted trail keeps the model's actual
                    # reasoning, not just what the tool call did.
                    new_messages = level_agent.memory.messages[pre_len:]
                    reasoning = next((m.content for m in new_messages if m.role == "assistant"), "") or ""
                    _emit(
                        "tool_call" if level_agent.tool_calls else "thought",
                        {"step": level_agent.current_step, "level": level_id, "reasoning": reasoning, "result": result},
                    )
                    if submit_tool is not None and level_id in submit_tool.accepted:
                        break

                if submit_tool is not None and level_id in submit_tool.accepted:
                    level_results[level_id] = submit_tool.accepted[level_id]
                elif submit_tool is not None and level_id in submit_tool.last_attempt:
                    # Never converged within its step budget: pass the last
                    # attempt through anyway, best-effort. The outer
                    # instrument.parse() reject-and-repair loop (unchanged,
                    # see guardrails.py) is the correctness backstop for
                    # whatever specific problems remain in it.
                    level_results[level_id] = submit_tool.last_attempt[level_id]
                else:
                    level_results[level_id] = {}

            return json.dumps({"levels": level_results})

    return SurveyPanelFlow


# ---------------------------------------------------------------------------
# "bwm_two_stage" flow (2026-09-01). Deliberately duplicated here, not
# imported, from symphysis/instruments/bwm_two_stage.py: this script runs in
# OpenManus's own isolated venv with zero Symphysis imports (see module
# docstring) and no path back to the parent package. Keep behaviorally
# identical to that module (covered by tests/test_bwm_two_stage.py in the
# parent interpreter) -- if the algorithm changes there, mirror the change
# here in the same commit.
# ---------------------------------------------------------------------------

_BEST_LINE_RE = re.compile(r"Best factor:\s*(?:<[^>]+>\s*)?([A-Za-z0-9_]+)", re.IGNORECASE)
_WORST_LINE_RE = re.compile(r"Worst factor:\s*(?:<[^>]+>\s*)?([A-Za-z0-9_]+)", re.IGNORECASE)


def _build_best_worst_prompt(codes, labels):
    dimension_list = "\n".join(f"- {c}: {labels.get(c, c)}" for c in codes)
    return (
        "You are comparing the following criteria:\n"
        f"{dimension_list}\n\n"
        "Which ONE criterion is BEST (most important), and which ONE is "
        "WORST (least important)? Answer in EXACTLY these two lines, using "
        f"the bare code only (one of {', '.join(codes)}), nothing else:\n"
        "Best factor: <CRITERION_CODE>\n"
        "Worst factor: <CRITERION_CODE>"
    )


def _parse_best_worst(text, codes):
    errors = []
    code_set = set(codes)
    best_match = _BEST_LINE_RE.search(text)
    worst_match = _WORST_LINE_RE.search(text)
    best = best_match.group(1) if best_match else None
    worst = worst_match.group(1) if worst_match else None
    if best is None:
        errors.append("No 'Best factor: <CRITERION_CODE>' line found")
    elif best not in code_set:
        errors.append(f"best={best!r} is not a known code {sorted(code_set)}")
        best = None
    if worst is None:
        errors.append("No 'Worst factor: <CRITERION_CODE>' line found")
    elif worst not in code_set:
        errors.append(f"worst={worst!r} is not a known code {sorted(code_set)}")
        worst = None
    if best is not None and worst is not None and best == worst:
        errors.append("best and worst must differ")
        best = worst = None
    return best, worst, errors


def _build_ratings_prompt(best, worst, others, labels):
    lines = [
        f"You said the BEST factor is {best} ({labels.get(best, best)}) "
        f"and the WORST factor is {worst} ({labels.get(worst, worst)})."
    ]
    lines.append(
        "Now state exactly the following ratings, each on a 1-9 integer "
        "scale (1 = equally important, 9 = extremely more important), "
        "one per line, in EXACTLY this format (replace only <N>):"
    )
    pairs = [(best, o) for o in others]
    pairs.append((best, worst))
    pairs.extend((o, worst) for o in others)
    for a, b in pairs:
        lines.append(f"{a} vs {b}: <N>")
    return "\n".join(lines)


def _pair_regex(a, b):
    return re.compile(rf"\b{re.escape(a)}\s+vs\.?\s+{re.escape(b)}\s*:\s*(\d+)", re.IGNORECASE)


def _parse_ratings(text, best, worst, others):
    errors = []
    ratings = {}
    pairs = [(best, o) for o in others]
    pairs.append((best, worst))
    pairs.extend((o, worst) for o in others)
    for a, b in pairs:
        match = _pair_regex(a, b).search(text)
        if match is None:
            errors.append(f"No explicit '{a} vs {b}: <N>' line found")
            continue
        value = int(match.group(1))
        if not (1 <= value <= 9):
            errors.append(f"{a} vs {b} = {value} is out of the required 1-9 range")
            continue
        ratings[(a, b)] = value
    return ratings, errors


def _assemble_bwm_payload(codes, best, worst, ratings, reasoning_text):
    others = [c for c in codes if c not in (best, worst)]
    best_to_others = {best: 1}
    for o in others:
        best_to_others[o] = ratings[(best, o)]
    best_to_others[worst] = ratings[(best, worst)]
    others_to_worst = {worst: 1}
    for o in others:
        others_to_worst[o] = ratings[(o, worst)]
    others_to_worst[best] = ratings[(best, worst)]
    return {
        "best": best,
        "worst": worst,
        "best_to_others": best_to_others,
        "others_to_worst": others_to_worst,
        "reasoning": reasoning_text,
    }


async def _run_bwm_two_stage(spec: dict, llm) -> None:
    """No agent, no tool loop: two plain llm.ask() completions, each parsed
    deterministically.

    A parse failure at either turn emits a "raw_completion" whose text is a
    deliberately-incomplete JSON object (never a fabricated/guessed value --
    it simply omits whatever field could not be determined) rather than an
    "error" event. This matters mechanically, not just stylistically:
    OpenManusProvider.complete() (runtime/openmanus.py) turns an "error"
    event into a raised OpenManusProviderError, which orchestrator.py
    catches at the PER-AGENT level -- skipping every remaining repeat for
    that agent entirely, not just this one malformed sample. A malformed
    "raw_completion", by contrast, flows into instrument.parse()
    (instruments/bwm.py), which flags the missing/invalid fields, which
    guardrails.py's existing reject-and-repair loop (unchanged) already
    knows how to retry per-sample -- exactly like a malformed completion
    from any other flow. 2026-09-01: the first version of this function
    used "error" events for parse failures and was live-validated only
    against a single non-RAG pilot agent that never hit this path; scaling
    to the full 12-agent panel immediately surfaced it via 3 agents (all at
    L2's 6 criteria, 2 of them RAG-enabled) hard-skipped on their very
    first malformed sample instead of getting the normal 3 retry attempts.

    Turn 2 is asked as a genuine follow-up in the SAME conversation (turn
    1's prompt, the model's own turn-1 answer, then turn 2's prompt), not a
    second independent call with no memory of turn 1: this both gives the
    model back its own stated best/worst as real context (not just restated
    in turn 2's prompt text) and keeps any reference material handed to
    turn 1 visible for turn 2's ratings too. context_chunks (RAG/knowledge-
    repo/role-pack material, when present) is prepended to turn 1's prompt
    for the same reason it would appear in any other flow's whole-response
    prompt -- 2026-09-01: an earlier version of this function silently
    dropped context_chunks entirely (it only ever looked at the "system"
    message, never the "user" message where that material lives), which
    would have made every RAG-enabled agent behave identically to its base
    counterpart. Caught before it reached a full-panel run."""
    from app.schema import Message

    codes = spec["codes"]
    labels = spec.get("labels", {})
    context_chunks = spec.get("context_chunks") or []
    system_content = next(
        (m.get("content", "") for m in spec["messages"] if m.get("role") == "system"), ""
    )
    system_msgs = [Message.system_message(system_content)] if system_content else None

    turn1_prompt = _build_best_worst_prompt(codes, labels)
    if context_chunks:
        joined = "\n\n---\n\n".join(context_chunks)
        # 2026-09-01: reference material placed before the task instructions
        # is not sufficient on its own -- live-observed at L2 (6 criteria):
        # mistral:7b, given a long RAG corpus chunk, answered with a prose
        # summary of the reference material instead of the required two
        # lines, in every one of several agents' first attempts (same root
        # cause diagnosed for the direct_completion backend in
        # instruments/bwm.py: long reference material invites the model to
        # describe/summarize it rather than perform the task that follows).
        # An explicit "do not summarize, answer only the format below"
        # directive right at the reference-material/task boundary is the
        # same fix pattern bwm.py already uses, applied here too.
        turn1_prompt = (
            f"Reference material to ground your judgement:\n\n{joined}\n\n"
            "Do not summarize or describe the reference material above. Answer ONLY the "
            f"question below, in exactly the two-line format requested:\n\n{turn1_prompt}"
        )

    conversation = [Message.user_message(turn1_prompt)]
    turn1_text = await llm.ask(conversation, system_msgs=system_msgs, stream=False)
    _emit("thought", {"step": 1, "reasoning": turn1_text, "result": "turn 1: best/worst elicitation"})

    best, worst, errors = _parse_best_worst(turn1_text, codes)
    if errors:
        payload = {"reasoning": f"[bwm_two_stage turn 1 parse failure: {'; '.join(errors)}] {turn1_text}"}
        _emit(
            "raw_completion",
            {"response": {"text": json.dumps(payload), "raw": {}, "model": llm.model, "finish_reason": "stop"}},
        )
        return

    conversation.append(Message.assistant_message(turn1_text))
    others = [c for c in codes if c not in (best, worst)]
    turn2_prompt = _build_ratings_prompt(best, worst, others, labels)
    conversation.append(Message.user_message(turn2_prompt))
    turn2_text = await llm.ask(conversation, system_msgs=system_msgs, stream=False)
    _emit("thought", {"step": 2, "reasoning": turn2_text, "result": "turn 2: pairwise ratings"})

    ratings, errors = _parse_ratings(turn2_text, best, worst, others)
    if errors:
        payload = {
            "best": best,
            "worst": worst,
            "reasoning": f"[bwm_two_stage turn 2 parse failure: {'; '.join(errors)}] {turn1_text}\n\n{turn2_text}",
        }
        _emit(
            "raw_completion",
            {"response": {"text": json.dumps(payload), "raw": {}, "model": llm.model, "finish_reason": "stop"}},
        )
        return

    payload = _assemble_bwm_payload(codes, best, worst, ratings, turn1_text + "\n\n" + turn2_text)
    _emit(
        "raw_completion",
        {"response": {"text": json.dumps(payload), "raw": {}, "model": llm.model, "finish_reason": "stop"}},
    )


def _build_survey_elicitation_agent_class():
    from app.agent.toolcall import ToolCallAgent
    from app.schema import ToolChoice
    from app.tool import Terminate, ToolCollection

    # 2026-09-01 diagnostic finding, isolated by a matched A/B curl test
    # directly against Ollama's OpenAI-compat endpoint (bypassing OpenManus
    # entirely, same model/tools/tool_choice=required both times): the
    # single sentence "State your reasoning before your final rating..."
    # in the system prompt reliably (3/3) made mistral:7b respond with
    # tool_calls=None and its answer folded into plain-text content instead
    # of a real structured tool call — even under tool_choice=REQUIRED.
    # Removing only that sentence produced a clean native tool_calls
    # response 3/3 times, same model, same tools, unchanged otherwise. The
    # model reliably treats "reason, then act" as license to answer in
    # prose and skip the tool call; this is not a model-capability ceiling
    # (the first curl test in this same diagnostic pass got a clean tool
    # call from mistral:7b on a bare prompt with no system message at all).
    # Fix: never ask for free-text reasoning as a step separate from the
    # tool call. Reasoning is captured as a field INSIDE the tool call's
    # own arguments instead (e.g. instrument_submit's own `reasoning`
    # field) — consistent with how instruments/bwm.py's direct_completion
    # JSON schema already asks for a `reasoning` field inside the same
    # structured answer, not as prose preceding it.
    SURVEY_ELICITATION_SYSTEM_PROMPT = (
        "You are a domain-expert panel member completing a structured survey "
        "instrument (e.g. a Best-Worst Method or AHP pairwise-comparison "
        "elicitation). You answer only from your own domain knowledge and any "
        "retrieved evidence you are given via tool calls; you never invent a "
        "citation you were not actually shown. Always answer by calling the "
        "appropriate tool — never as plain text. Include your reasoning as "
        "part of the tool call's own arguments (its `reasoning` field) so "
        "the trail this agent produces is auditable, not just its answer."
    )

    # `CreateChatCompletion` (a second, generically-worded "give a text
    # response" tool OpenManus ships by default alongside Terminate) was
    # also confirmed to worsen the same failure in this diagnostic pass:
    # offered alongside Terminate, the model would call CreateChatCompletion
    # and stuff the intended terminate(...) call inside it as literal text
    # rather than invoking Terminate directly. Neither tool is needed for a
    # survey-elicitation agent (its only legitimate terminal actions are
    # Terminate or, in panel mode, instrument_submit), so it is dropped
    # here rather than worked around. tool_choice=REQUIRED (below) is kept
    # as a second, independent layer of defense on top of the prompt fix
    # above — both were confirmed individually to matter in this pass.
    NEXT_STEP_PROMPT = (
        "If you have reached your final answer for this step, you MUST "
        "record it via a tool call (instrument_submit if it is offered, "
        "otherwise terminate) — do not just restate the answer as plain "
        "text without calling the tool."
    )

    class SurveyElicitationAgent(ToolCallAgent):
        # This whole class exists only here, never in runtime/openmanus.py:
        # this script runs in a separate interpreter that never has the
        # `symphysis` package on its path (see module docstring), so there
        # is nothing on the runtime/openmanus.py side to mirror against —
        # the subprocess boundary IS the design, not an accident of it.
        name: str = "survey_elicitation"
        description: str = (
            "an expert panel agent that completes one Symphysis survey instrument, "
            "grounding its answers in retrieved evidence and declaring its reasoning."
        )
        system_prompt: str = SURVEY_ELICITATION_SYSTEM_PROMPT
        next_step_prompt: str = NEXT_STEP_PROMPT
        available_tools: "ToolCollection" = ToolCollection(Terminate())
        tool_choices: str = ToolChoice.REQUIRED
        max_steps: int = 15

    return SurveyElicitationAgent


async def _run(spec: dict) -> None:
    from app.config import LLMSettings
    from app.llm import LLM
    from app.schema import AgentState, Message
    from app.tool import Terminate, ToolCollection

    SurveyElicitationAgent = _build_survey_elicitation_agent_class()

    # LLM.__init__ (vendor/openmanus/app/llm.py) does
    # `llm_config.get(config_name, llm_config["default"])` — despite its own
    # `llm_config: Optional[LLMSettings]` type hint, it actually requires a
    # Dict[str, LLMSettings] (matching AppConfig.llm's real type,
    # vendor/openmanus/app/config.py's `llm: Dict[str, LLMSettings]`), with
    # both the requested config_name AND a "default" key present — a bare
    # LLMSettings instance raises AttributeError ('LLMSettings' object has
    # no attribute 'get'). Both keys point at the same settings here since
    # this driver has exactly one model per run.
    settings = LLMSettings(**spec["llm_settings"])
    llm = LLM(config_name=spec["config_name"], llm_config={spec["config_name"]: settings, "default": settings})

    if spec.get("flow") == "bwm_two_stage":
        # No SurveyElicitationAgent/ToolCallAgent construction needed at all:
        # this flow never calls a tool, so it only needs the raw LLM client.
        await _run_bwm_two_stage(spec, llm)
        return

    is_panel = spec.get("flow") == "survey_panel"
    agent_kwargs = {"llm": llm, "max_steps": spec.get("max_steps", 15)}
    proxy_port = spec.get("proxy_port")
    available_tools = spec.get("available_tools") or []
    if proxy_port and available_tools:
        ProxyTool = _build_proxy_tool_class()
        # In panel mode, "instrument_submit" gets the bookkeeping subclass
        # (see _build_instrument_submit_proxy_tool_class's docstring);
        # every other tool (rag_retrieval, web_search, citation_verify, ...)
        # is unaffected and still uses the plain ProxyTool either way.
        InstrumentSubmitProxyTool = _build_instrument_submit_proxy_tool_class(ProxyTool) if is_panel else None
        proxy_tools = [
            (InstrumentSubmitProxyTool if is_panel and t["name"] == "instrument_submit" else ProxyTool)(
                name=t["name"],
                description=t["description"],
                parameters=t.get("parameters"),
                proxy_port=proxy_port,
                proxy_tool_name=t["name"],
            )
            for t in available_tools
        ]
        agent_kwargs["available_tools"] = ToolCollection(Terminate(), *proxy_tools)

    agent = SurveyElicitationAgent(**agent_kwargs)

    if is_panel:
        SurveyPanelFlow = _build_survey_panel_flow_class()
        flow = SurveyPanelFlow(
            agent,
            levels=spec["levels"],
            level_messages=spec["level_messages"],
            level_max_steps=spec.get("level_max_steps", 5),
        )
        final_text = await flow.execute("")
        _emit(
            "raw_completion",
            {"response": {"text": final_text, "raw": {}, "model": agent.llm.model, "finish_reason": "stop"}},
        )
        return

    for msg in spec["messages"]:
        role, content = msg.get("role", "user"), msg.get("content", "")
        if role == "system":
            continue  # system_prompt is already set on the agent class
        agent.memory.add_message(Message.user_message(content) if role == "user" else Message.assistant_message(content))

    while agent.state != AgentState.FINISHED and agent.current_step < agent.max_steps:
        pre_len = len(agent.memory.messages)
        result = await agent.step()
        agent.current_step += 1
        new_messages = agent.memory.messages[pre_len:]
        reasoning = next((m.content for m in new_messages if m.role == "assistant"), "") or ""
        _emit(
            "tool_call" if agent.tool_calls else "thought",
            {"step": agent.current_step, "reasoning": reasoning, "result": result},
        )

    final_message = agent.memory.messages[-1].content if agent.memory.messages else ""
    _emit(
        "raw_completion",
        {"response": {"text": final_message, "raw": {}, "model": agent.llm.model, "finish_reason": "stop"}},
    )


def main() -> int:
    input_path = Path(sys.argv[1])
    spec = json.loads(input_path.read_text(encoding="utf-8"))
    try:
        asyncio.run(_run(spec))
    except Exception as exc:  # noqa: BLE001 — deliberately broad: any failure must reach the parent as an event
        _emit("error", {"message": f"{type(exc).__name__}: {exc}"})
        return 0  # the error event itself is the signal; see module docstring
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
