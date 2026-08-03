"""SAGE (Survey Agent Generation Engine) web backend.

    uvicorn web.backend.main:app --reload --port 8000

Serves the REST API the React frontend (web/frontend/) talks to. Business
logic lives entirely in the agentic_survey package under src/; this layer
is thin: HTTP in, JSON out, path/ID sanitisation, background-run tracking.
"""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import paths  # noqa: F401 - import for its sys.path side effect
from .routers import agents, knowledge, library, proposer, settings, surveys

from agentic_survey import app_config  # noqa: E402 - must follow the `paths` import above

# Restore any previously-saved LLM endpoint/API keys before anything else
# runs, so those settings survive a backend restart instead of silently
# reverting to localhost / no keys.
settings.load_settings_into_env()

app = FastAPI(title="SAGE API", version="0.1.0")

# Origins the frontend may be served from. Defaults (config/defaults.yaml's
# cors.default_origins, overridable via Settings -> Config) cover local
# Vite dev; CORS_EXTRA_ORIGINS (comma-separated env var) adds more, e.g.
# when the UI is reached over Tailscale at the server's own IP instead of
# localhost -- that's a deployment-time concern, appropriately an env var
# rather than a versioned config value.
_default_origins = app_config.get_config().get("cors", {}).get("default_origins", ["http://localhost:5173", "http://127.0.0.1:5173"])
_extra_origins = [o.strip() for o in os.environ.get("CORS_EXTRA_ORIGINS", "").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_default_origins + _extra_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(surveys.router)
app.include_router(agents.router)
app.include_router(library.router)
app.include_router(proposer.router)
app.include_router(knowledge.router)
app.include_router(settings.router)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}
