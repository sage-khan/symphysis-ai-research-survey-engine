"""agentic-survey-tool web backend.

    uvicorn web.backend.main:app --reload --port 8000

Serves the REST API the React frontend (web/frontend/) talks to. Business
logic lives entirely in the agentic_survey package under src/; this layer
is thin: HTTP in, JSON out, path/ID sanitisation, background-run tracking.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import paths  # noqa: F401 - import for its sys.path side effect
from .routers import agents, surveys

app = FastAPI(title="agentic-survey-tool API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(surveys.router)
app.include_router(agents.router)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}
