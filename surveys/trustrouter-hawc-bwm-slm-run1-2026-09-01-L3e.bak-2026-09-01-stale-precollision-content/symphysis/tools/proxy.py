"""Local-only HTTP bridge letting an isolated-subprocess runtime backend
(OpenManus, driven under vendor/openmanus/.venv — see runtime/openmanus.py
and runtime/_openmanus_driver.py) call back into THIS process's own real
tools (RAG retrieval, web search, citation verification).

Why a bridge exists at all: the tools themselves (tools/registry.py) and
the capability authorization check (tools/authorization.py) only exist in
this process — the isolated subprocess deliberately has zero `symphysis`
import (see `_openmanus_driver.py`'s module docstring), so it cannot call
either directly. This is the seam: bound to 127.0.0.1 only, an ephemeral
port, one server per agent run, started right before the subprocess is
launched and torn down as soon as it exits.

Uses only the stdlib (`http.server.ThreadingHTTPServer`) rather than
FastAPI/uvicorn: `orchestrator.py`'s survey-run loop is fully synchronous,
and this bridge's entire job is to sit in a background thread answering a
handful of POSTs while the main thread blocks reading the subprocess's
stdout — bringing in an ASGI event loop for that would be more machinery
than the job needs.
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import TYPE_CHECKING, Dict

from .authorization import ToolAuthorizationError, check_capability
from .registry import ToolSpec

if TYPE_CHECKING:
    from ..audit.logger import SurveyStorage


class ToolProxyServer:
    def __init__(self, storage: "SurveyStorage", agent_id: str, tools: Dict[str, ToolSpec]) -> None:
        self._storage = storage
        self._agent_id = agent_id
        self._tools = tools
        self._httpd = ThreadingHTTPServer(("127.0.0.1", 0), self._make_handler())
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)

    @property
    def port(self) -> int:
        return self._httpd.server_address[1]

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._httpd.shutdown()
        self._httpd.server_close()

    def __enter__(self) -> "ToolProxyServer":
        self.start()
        return self

    def __exit__(self, *exc_info) -> None:
        self.stop()

    def _make_handler(self):
        tools = self._tools
        storage = self._storage
        agent_id = self._agent_id

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format: str, *args: object) -> None:
                # Quiet: every real call is already logged to
                # conversation.jsonl by the tool itself (tools/registry.py),
                # so a second HTTP access log would only be noise.
                pass

            def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler's naming convention
                tool_name = self.path.strip("/").rsplit("/", 1)[-1]
                length = int(self.headers.get("Content-Length", 0))
                try:
                    body = json.loads(self.rfile.read(length) or b"{}")
                except ValueError:
                    self._respond(400, {"error": "request body is not valid JSON"})
                    return

                spec = tools.get(tool_name)
                if spec is None:
                    self._respond(404, {"error": f"unknown tool {tool_name!r}; registered: {sorted(tools)}"})
                    return

                try:
                    check_capability(storage, agent_id, spec.capability)
                    result = spec.execute(**body)
                except ToolAuthorizationError as exc:
                    self._respond(403, {"error": str(exc)})
                    return
                except Exception as exc:  # noqa: BLE001 - any tool failure must reach the caller as a response, not a crash
                    self._respond(500, {"error": f"{type(exc).__name__}: {exc}"})
                    return
                self._respond(200, result)

            def _respond(self, status: int, payload: Dict[str, object]) -> None:
                body = json.dumps(payload).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        return Handler
