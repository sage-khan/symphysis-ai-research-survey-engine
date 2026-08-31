"""Tests for tools/proxy.py's ToolProxyServer: a real HTTP server bound to
127.0.0.1, exercised with real requests (not mocked), since its entire job
is being a genuine network-callable bridge for the isolated OpenManus
subprocess (see runtime/openmanus.py)."""

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest
import requests

from symphysis.agent_card import ModelSpec, new_card
from symphysis.audit.logger import SurveyStorage
from symphysis.policy.capability import WEB_SEARCH
from symphysis.runtime.openmanus import _DRIVER_SCRIPT, _ISOLATED_VENV_PYTHON, isolated_venv_ready
from symphysis.spawning import spawn
from symphysis.tools.proxy import ToolProxyServer
from symphysis.tools.registry import ToolSpec


def _card(tmp_path: Path, agent_id: str = "proxy-test-agent", **kwargs):
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("Role: {role}\n{role_description}\n", encoding="utf-8")
    return new_card(
        agent_id=agent_id,
        role="Data Engineer",
        role_description="A test persona.",
        system_prompt_template=str(prompt),
        model=ModelSpec(provider="ollama", name="test-model"),
        did_seed="test-seed",
        **kwargs,
    )


def test_proxy_calls_a_registered_tool_and_returns_its_json_result(tmp_path):
    card = _card(tmp_path, tools=["web_search"])
    storage = SurveyStorage(tmp_path / "survey")
    spawn.declare_root(storage, card, survey_id="test-survey")

    calls = []

    def _fake_web_search(query, top_k=5):
        calls.append((query, top_k))
        return {"results": [{"title": "t", "url": "u", "content": "c"}]}

    tools = {"web_search": ToolSpec(name="web_search", capability=WEB_SEARCH, execute=_fake_web_search)}

    with ToolProxyServer(storage, card.agent_id, tools) as server:
        resp = requests.post(f"http://127.0.0.1:{server.port}/tools/web_search", json={"query": "wind energy"})

    assert resp.status_code == 200
    assert resp.json() == {"results": [{"title": "t", "url": "u", "content": "c"}]}
    assert calls == [("wind energy", 5)]


def test_proxy_returns_403_when_capability_not_granted(tmp_path):
    card = _card(tmp_path)  # web_search NOT in tools=[], so not granted
    storage = SurveyStorage(tmp_path / "survey")
    spawn.declare_root(storage, card, survey_id="test-survey")

    tools = {"web_search": ToolSpec(name="web_search", capability=WEB_SEARCH, execute=lambda **kw: {})}

    with ToolProxyServer(storage, card.agent_id, tools) as server:
        resp = requests.post(f"http://127.0.0.1:{server.port}/tools/web_search", json={"query": "x"})

    assert resp.status_code == 403
    assert "was not granted capability" in resp.json()["error"]


def test_proxy_returns_404_for_unknown_tool(tmp_path):
    card = _card(tmp_path)
    storage = SurveyStorage(tmp_path / "survey")
    spawn.declare_root(storage, card, survey_id="test-survey")

    with ToolProxyServer(storage, card.agent_id, {}) as server:
        resp = requests.post(f"http://127.0.0.1:{server.port}/tools/does_not_exist", json={})

    assert resp.status_code == 404


def test_proxy_returns_500_when_the_tool_itself_raises(tmp_path):
    card = _card(tmp_path, tools=["web_search"])
    storage = SurveyStorage(tmp_path / "survey")
    spawn.declare_root(storage, card, survey_id="test-survey")

    def _boom(**kw):
        raise RuntimeError("something broke")

    tools = {"web_search": ToolSpec(name="web_search", capability=WEB_SEARCH, execute=_boom)}

    with ToolProxyServer(storage, card.agent_id, tools) as server:
        resp = requests.post(f"http://127.0.0.1:{server.port}/tools/web_search", json={"query": "x"})

    assert resp.status_code == 500
    assert "something broke" in resp.json()["error"]


@pytest.mark.skipif(
    not isolated_venv_ready(),
    reason="vendor/openmanus/.venv not set up; see the plan doc's isolated-venv setup step",
)
def test_openmanus_driver_proxy_tool_reaches_the_real_server_across_the_process_boundary(tmp_path):
    """The strongest possible test of the tool-bridge plumbing short of a
    live model call: starts a REAL ToolProxyServer in this process, then
    runs a tiny script under the isolated venv's own interpreter that
    imports _openmanus_driver.py, builds a ProxyTool exactly as _run() does,
    and calls its async execute() for real — over a real HTTP request,
    across a real process boundary, exercising httpx (an OpenManus
    dependency, not this repo's) end to end."""
    card = _card(tmp_path, tools=["web_search"])
    storage = SurveyStorage(tmp_path / "survey")
    spawn.declare_root(storage, card, survey_id="test-survey")

    calls = []

    def _fake_web_search(query, top_k=5):
        calls.append(query)
        return {"results": [{"title": "Wind Energy Spain", "url": "https://example.org", "content": "..."}]}

    tools = {"web_search": ToolSpec(name="web_search", capability=WEB_SEARCH, execute=_fake_web_search)}

    driver_dir = _DRIVER_SCRIPT.parent
    script = f"""
import asyncio, json, sys
sys.path.insert(0, {str(driver_dir)!r})
import _openmanus_driver as d
ProxyTool = d._build_proxy_tool_class()
tool = ProxyTool(name="web_search", description="", parameters=None, proxy_port={{port}}, proxy_tool_name="web_search")
result = asyncio.run(tool.execute(query="wind energy Spain"))
print(json.dumps({{"output": result.output, "error": result.error}}))
"""

    with ToolProxyServer(storage, card.agent_id, tools) as server:
        proc = subprocess.run(
            [str(_ISOLATED_VENV_PYTHON), "-c", script.replace("{port}", str(server.port))],
            capture_output=True,
            text=True,
            timeout=30,
        )

    assert proc.returncode == 0, proc.stderr
    printed = json.loads(proc.stdout.strip().splitlines()[-1])
    assert printed["error"] is None
    assert "Wind Energy Spain" in printed["output"]
    assert calls == ["wind energy Spain"]
