"""Real cross-process integration test for _openmanus_driver.py's
SurveyPanelFlow/InstrumentSubmitProxyTool (Phase 3, plan doc tasks 17-19):
starts a REAL tools/proxy.py ToolProxyServer in this process, wired to a
REAL HierarchicalBWMInstrument (not a mock), then runs a script under the
isolated venv's own interpreter that imports _openmanus_driver.py and
drives SurveyPanelFlow.execute() against a small scripted fake agent
standing in for the LLM (see the script below for why: this test verifies
SurveyPanelFlow's OWN orchestration logic — per-level submission gating,
last_attempt fallback, final JSON assembly — not OpenManus's ToolCallAgent
step() internals, which are OpenManus's own tested code, not this
integration's). Every instrument_submit call in this test crosses the real
process boundary via real HTTP, hitting the real per-level validator."""

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest

from symphysis.agent_card import ModelSpec, new_card
from symphysis.audit.logger import SurveyStorage
from symphysis.instruments.hierarchical_bwm import HierarchicalBWMInstrument
from symphysis.runtime.openmanus import _DRIVER_SCRIPT, _ISOLATED_VENV_PYTHON, isolated_venv_ready
from symphysis.spawning import spawn
from symphysis.tools.proxy import ToolProxyServer
from symphysis.tools.registry import build_registry

PANEL_PARAMS = {
    "levels": [
        {"id": "L1", "name": "Top-level factors", "description": "d1", "dimensions": ["DVS", "F"]},
        {"id": "L2", "name": "Second level", "description": "d2", "dimensions": ["A", "B"]},
    ],
}


def _card(tmp_path: Path, agent_id: str = "panel-flow-agent"):
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("Role: {role}\n{role_description}\n", encoding="utf-8")
    return new_card(
        agent_id=agent_id,
        role="Data Engineer",
        role_description="A test persona.",
        system_prompt_template=str(prompt),
        model=ModelSpec(provider="ollama", name="test-model"),
        did_seed="test-seed",
        runtime_backend="openmanus",
    )


_DRIVER_SCRIPT_TEMPLATE = """
import asyncio, json, sys
sys.path.insert(0, {driver_dir!r})
import _openmanus_driver as d
from app.config import LLMSettings
from app.llm import LLM
from app.schema import AgentState

ProxyTool = d._build_proxy_tool_class()
InstrumentSubmitProxyTool = d._build_instrument_submit_proxy_tool_class(ProxyTool)
SurveyPanelFlow = d._build_survey_panel_flow_class()
SurveyElicitationAgent = d._build_survey_elicitation_agent_class()

submit_tool = InstrumentSubmitProxyTool(
    name="instrument_submit", description="", parameters=None,
    proxy_port={proxy_port}, proxy_tool_name="instrument_submit",
)
from app.tool import ToolCollection
tools = ToolCollection(submit_tool)


class ScriptedAgent(SurveyElicitationAgent):
    \"\"\"A real BaseAgent subclass (required: BaseFlow.agents is typed
    Dict[str, BaseAgent], so pydantic rejects any non-BaseAgent stand-in
    even with arbitrary_types_allowed on BaseFlow itself) with step()
    overridden to a scripted sequence instead of a real LLM call. This
    test targets SurveyPanelFlow's OWN orchestration (submission gating,
    last_attempt fallback, JSON assembly) — not OpenManus's already-tested
    ToolCallAgent.step() internals — so replacing just that one method,
    driven by a marker embedded in the level's first message content
    (this test's level_messages below), is the correct isolation.\"\"\"

    directive: str = ""
    level_id: str = ""
    step_count: int = 0

    async def step(self):
        self.step_count += 1
        if not self.directive:
            _, self.level_id, self.directive = self.memory.messages[0].content.split(":")
        tool = self.available_tools.get_tool("instrument_submit")
        if self.directive == "reject_then_accept":
            if self.step_count == 1:
                await tool.execute(
                    level_id=self.level_id, best="DVS", worst="F",
                    best_to_others={{"DVS": 9, "F": 3}},  # self-rating mistake -> rejected
                    others_to_worst={{"DVS": 3, "F": 1}}, reasoning="first try",
                )
            else:
                await tool.execute(
                    level_id=self.level_id, best="DVS", worst="F",
                    best_to_others={{"DVS": 1, "F": 3}},
                    others_to_worst={{"DVS": 3, "F": 1}}, reasoning="corrected",
                )
                self.state = AgentState.FINISHED
        elif self.directive == "never_accept":
            await tool.execute(
                level_id=self.level_id, best="A", worst="B",
                best_to_others={{"A": 9, "B": 3}},  # always wrong -> never accepted
                others_to_worst={{"A": 3, "B": 1}}, reasoning="always wrong",
            )
        return "stepped"


# A real LLM instance is required by BaseAgent's field typing, but is never
# actually called: ScriptedAgent.step() above replaces the only method that
# would call it.
settings = LLMSettings(
    model="test", base_url="http://127.0.0.1:1/v1", api_key="x",
    max_tokens=64, temperature=0.7, api_type="ollama", api_version="",
)
llm = LLM(config_name="scripted-panel-test", llm_config={{"scripted-panel-test": settings, "default": settings}})

primary_agent = ScriptedAgent(llm=llm, available_tools=tools, max_steps=5)
flow = SurveyPanelFlow(
    primary_agent,
    levels={levels!r},
    level_messages={level_messages!r},
    level_max_steps=3,
)
final_text = asyncio.run(flow.execute(""))
print(final_text)
"""


@pytest.mark.skipif(
    not isolated_venv_ready(),
    reason="vendor/openmanus/.venv not set up; see the plan doc's isolated-venv setup step",
)
def test_survey_panel_flow_accepts_a_corrected_level_and_falls_back_on_a_never_accepted_one(tmp_path):
    card = _card(tmp_path)
    storage = SurveyStorage(tmp_path / "survey")
    spawn.declare_root(storage, card, survey_id="test-survey")

    instrument = HierarchicalBWMInstrument()

    class _FakeAgentForRegistry:
        # build_registry() only reads agent.card/agent.storage/agent._retriever/
        # agent._knowledge_repo_retriever for its other tools; None is fine here
        # since this test only needs instrument_submit registered.
        def __init__(self):
            self.card = card
            self.storage = storage
            self._retriever = None
            self._knowledge_repo_retriever = None

    tools = build_registry(_FakeAgentForRegistry(), instrument=instrument, instrument_params=PANEL_PARAMS)
    assert "instrument_submit" in tools

    levels = PANEL_PARAMS["levels"]
    level_messages = {
        "L1": [{"role": "user", "content": "marker:L1:reject_then_accept"}],
        "L2": [{"role": "user", "content": "marker:L2:never_accept"}],
    }

    driver_dir = _DRIVER_SCRIPT.parent
    script = _DRIVER_SCRIPT_TEMPLATE.format(
        driver_dir=str(driver_dir),
        proxy_port="{port}",
        levels=levels,
        level_messages=level_messages,
    )

    with ToolProxyServer(storage, card.agent_id, tools) as server:
        proc = subprocess.run(
            [str(_ISOLATED_VENV_PYTHON), "-c", script.replace("{port}", str(server.port))],
            capture_output=True,
            text=True,
            timeout=30,
        )

    assert proc.returncode == 0, proc.stderr
    final_text = proc.stdout.strip().splitlines()[-1]
    payload = json.loads(final_text)

    # L1: rejected once (self-rating mistake), corrected on the 2nd
    # submission, accepted -> the ACCEPTED (corrected) answer is used.
    l1 = payload["levels"]["L1"]
    assert l1["best_to_others"]["DVS"] == 1

    # L2: never submitted a valid answer within its 3-step budget -> the
    # LAST ATTEMPT is used as a best-effort fallback (still wrong, exactly
    # as submitted, for the outer reject-and-repair loop to catch).
    l2 = payload["levels"]["L2"]
    assert l2["best_to_others"]["A"] == 9

    # The whole-response payload validates through the SAME instrument
    # this flow's instrument_submit calls used, confirming the final JSON
    # really is shaped the way parse() expects, correctly for L1 and
    # (deliberately, per the never_accept script) still wrong for L2.
    result = instrument.parse(final_text, PANEL_PARAMS)
    assert not result.valid
    assert any("L2" in e for e in result.errors)
    assert not any("L1" in e for e in result.errors)
