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
  ]
}

Output: one JSON object per line on stdout (NDJSON), flushed immediately so
the parent process can stream events as they occur:
  {"kind": "thought"|"tool_call", "payload": {"step": N, "result": "..."}}
  {"kind": "raw_completion", "payload": {"response": {...}}}   # exactly one, last
  {"kind": "error", "payload": {"message": "..."}}             # only on failure
Exit code is 0 on a clean run (including one that ends in an "error" event
for an OpenManus-internal failure), nonzero only for a driver-level crash
before any output was produced (e.g. malformed input JSON).
"""

from __future__ import annotations

import asyncio
import json
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


def _build_survey_elicitation_agent_class():
    from app.agent.toolcall import ToolCallAgent
    from app.tool import CreateChatCompletion, Terminate, ToolCollection

    SURVEY_ELICITATION_SYSTEM_PROMPT = (
        "You are a domain-expert panel member completing a structured survey "
        "instrument (e.g. a Best-Worst Method or AHP pairwise-comparison "
        "elicitation). You answer only from your own domain knowledge and any "
        "retrieved evidence you are given via tool calls; you never invent a "
        "citation you were not actually shown. State your reasoning before "
        "your final rating so the trail this agent produces is auditable, "
        "not just its answer."
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
        next_step_prompt: str = ""
        available_tools: "ToolCollection" = ToolCollection(CreateChatCompletion(), Terminate())
        max_steps: int = 15

    return SurveyElicitationAgent


async def _run(spec: dict) -> None:
    from app.config import LLMSettings
    from app.llm import LLM
    from app.schema import AgentState, Message
    from app.tool import CreateChatCompletion, Terminate, ToolCollection

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

    agent_kwargs = {"llm": llm, "max_steps": spec.get("max_steps", 15)}
    proxy_port = spec.get("proxy_port")
    available_tools = spec.get("available_tools") or []
    if proxy_port and available_tools:
        ProxyTool = _build_proxy_tool_class()
        proxy_tools = [
            ProxyTool(
                name=t["name"],
                description=t["description"],
                parameters=t.get("parameters"),
                proxy_port=proxy_port,
                proxy_tool_name=t["name"],
            )
            for t in available_tools
        ]
        agent_kwargs["available_tools"] = ToolCollection(CreateChatCompletion(), Terminate(), *proxy_tools)

    agent = SurveyElicitationAgent(**agent_kwargs)

    for msg in spec["messages"]:
        role, content = msg.get("role", "user"), msg.get("content", "")
        if role == "system":
            continue  # system_prompt is already set on the agent class
        agent.memory.add_message(Message.user_message(content) if role == "user" else Message.assistant_message(content))

    while agent.state != AgentState.FINISHED and agent.current_step < agent.max_steps:
        result = await agent.step()
        agent.current_step += 1
        _emit("tool_call" if agent.tool_calls else "thought", {"step": agent.current_step, "result": result})

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
