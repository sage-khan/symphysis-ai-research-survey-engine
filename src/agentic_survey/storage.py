"""Per-survey / per-agent persistent folder layout.

surveys/<survey-id>/
    survey.yaml
    agents/<agent-id>/
        config.yaml         # copy of the config actually used for this run
        did.json
        conversation.jsonl  # one line per raw completion attempt (accepted or rejected)
        thoughts.md          # human-readable reasoning trace, accepted samples only
        samples/sample_NN.json / .md
        result.json          # final accepted InstrumentResult set + guardrail summary
    report/
        report.md
        charts/*.png
        combined_results.json
"""

from __future__ import annotations

import json
import shutil
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from .did import AgentDID
from .guardrails import GuardedRun
from .providers.base import ProviderResponse


class SurveyStorage:
    def __init__(self, survey_root: Path) -> None:
        self.root = survey_root
        self.agents_dir = self.root / "agents"
        self.report_dir = self.root / "report"
        self.report_dir.mkdir(parents=True, exist_ok=True)
        (self.report_dir / "charts").mkdir(parents=True, exist_ok=True)

    def agent_dir(self, agent_id: str) -> Path:
        d = self.agents_dir / agent_id
        (d / "samples").mkdir(parents=True, exist_ok=True)
        return d

    def init_agent(self, agent_id: str, config_source: Path) -> AgentDID:
        d = self.agent_dir(agent_id)
        shutil.copy(config_source, d / "config.yaml")
        return AgentDID.load_or_create(d / "did.json", agent_id)

    def append_conversation(self, agent_id: str, entry: Dict[str, Any]) -> None:
        d = self.agent_dir(agent_id)
        entry = {**entry, "logged_at": datetime.now(timezone.utc).isoformat()}
        with (d / "conversation.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    def write_guarded_run(self, agent_id: str, run: GuardedRun) -> None:
        d = self.agent_dir(agent_id)

        for i, response in enumerate(run.raw_completions):
            self.append_conversation(agent_id, {"kind": "raw_completion", "index": i, "response": _response_dict(response)})
        for i, rej in enumerate(run.rejected):
            self.append_conversation(agent_id, {"kind": "rejected", "index": i, **rej})

        thoughts_lines = [f"# Reasoning trace: {agent_id}\n"]
        for i, result in enumerate(run.accepted):
            sample_path_json = d / "samples" / f"sample_{i:02d}.json"
            sample_path_md = d / "samples" / f"sample_{i:02d}.md"
            sample_path_json.write_text(json.dumps(result.payload, indent=2), encoding="utf-8")
            reasoning = result.payload.get("reasoning", "(no reasoning field returned)")
            sample_path_md.write_text(
                f"# Sample {i}\n\n"
                f"- Best: {result.payload.get('best')}\n"
                f"- Worst: {result.payload.get('worst')}\n\n"
                f"## Reasoning\n\n{reasoning}\n",
                encoding="utf-8",
            )
            thoughts_lines.append(f"## Sample {i}\n\n{reasoning}\n")
        (d / "thoughts.md").write_text("\n".join(thoughts_lines), encoding="utf-8")

        result_summary = {
            "agent_id": agent_id,
            "accepted_count": len(run.accepted),
            "rejected_count": len(run.rejected),
            "flagged_low_agreement": run.flagged_low_agreement,
            "accepted_payloads": [r.payload for r in run.accepted],
        }
        (d / "result.json").write_text(json.dumps(result_summary, indent=2), encoding="utf-8")

    def write_report(self, markdown: str) -> Path:
        path = self.report_dir / "report.md"
        path.write_text(markdown, encoding="utf-8")
        return path

    def write_combined_results(self, data: Dict[str, Any]) -> Path:
        path = self.report_dir / "combined_results.json"
        path.write_text(json.dumps(data, indent=2, default=_json_default), encoding="utf-8")
        return path


def _response_dict(response: ProviderResponse) -> Dict[str, Any]:
    return {"text": response.text, "model": response.model, "finish_reason": response.finish_reason, "raw": response.raw}


def _json_default(obj: Any) -> Any:
    if hasattr(obj, "tolist"):
        return obj.tolist()
    return str(obj)
