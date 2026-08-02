"""Per-survey / per-agent persistent folder layout.

surveys/<survey-id>/
    survey.yaml
    agents/<agent-id>.json   # the portable Agent Card (source config)
    agents/<agent-id>/       # written at runtime:
        card.json             #   copy of the card actually used for this run
        did.json              #   this agent's did:key + public key (from the card)
        prompt.md             #   the exact outgoing prompt (system + user messages), every provider
        conversation.jsonl    #   one line per event: raw completion, rejection, or tool_call (RAG retrieval)
        thoughts.md           #   human-readable reasoning trace, accepted samples only
        samples/sample_NN.json / .md
        filled_survey.md      #   the consolidated, human-readable completed survey across all accepted samples
        result.json           #   final accepted InstrumentResult set + guardrail summary
    report/
        report.md
        charts/*.png
        combined_results.json

Every file here is plain text (Markdown/JSON/JSONL) by design, so the full
trace of what an agent was asked, what it retrieved, what it answered, and
why is readable and diffable on any platform without this app installed.
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from .agent_card import AgentCard
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

    def init_agent(self, card: AgentCard, card_source: Path) -> None:
        d = self.agent_dir(card.agent_id)
        shutil.copy(card_source, d / "card.json")
        (d / "did.json").write_text(
            json.dumps(
                {
                    "agent_id": card.agent_id,
                    "did": card.did.id,
                    "method": card.did.method,
                    "public_key_multibase": card.did.public_key_multibase,
                    "deterministic": card.did.deterministic,
                    "seed_derivation": card.did.seed_derivation,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    def append_conversation(self, agent_id: str, entry: Dict[str, Any]) -> None:
        d = self.agent_dir(agent_id)
        entry = {**entry, "logged_at": datetime.now(timezone.utc).isoformat()}
        with (d / "conversation.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    def write_prompt(self, agent_id: str, messages: List[Dict[str, str]]) -> None:
        """The exact outgoing prompt, for every provider (not only the manual
        one, which already writes its own copy for the human to paste into a
        chat UI). Written once per agent since the same messages are reused
        across all of that agent's repeated samples."""
        d = self.agent_dir(agent_id)
        parts = [f"# Prompt sent to {agent_id}\n"]
        for msg in messages:
            parts.append(f"## {msg['role']}\n\n{msg['content']}\n")
        (d / "prompt.md").write_text("\n".join(parts), encoding="utf-8")

    def write_tool_call(self, agent_id: str, tool: str, detail: Dict[str, Any]) -> None:
        """Log a discrete tool-use event (currently: RAG retrieval) into the
        same conversation trace as completions/rejections, so 'what tools
        were used, how, when, and on what' is answerable from one file."""
        self.append_conversation(agent_id, {"kind": "tool_call", "tool": tool, **detail})

    def write_introduction(self, agent_id: str, response: ProviderResponse) -> None:
        """Logged as this agent's very first conversation-trace entry (see
        Agent.introduce): the agent's own stated understanding of who it is
        and what it's being asked to do, before any Best/Worst attempt, so a
        human reviewer can check comprehension at a glance instead of
        inferring it from terse per-sample reasoning."""
        self.append_conversation(agent_id, {"kind": "introduction", "response": _response_dict(response)})

    def write_guarded_run(
        self,
        agent_id: str,
        run: GuardedRun,
        card: AgentCard | None = None,
        instrument_params: Dict[str, Any] | None = None,
    ) -> None:
        d = self.agent_dir(agent_id)

        for i, response in enumerate(run.raw_completions):
            self.append_conversation(agent_id, {"kind": "raw_completion", "index": i, "response": _response_dict(response)})
        for i, rej in enumerate(run.rejected):
            self.append_conversation(agent_id, {"kind": "rejected", "index": i, **rej})

        total_attempts = len(run.accepted) + len(run.rejected)
        thoughts_lines = [
            f"# Reasoning trace: {agent_id}\n",
            "**What a \"Sample\" is:** this agent was asked the exact same Best-Worst "
            f"comparison task independently {total_attempts} time(s) in total (not a sequence "
            "of different questions) -- repeated, independent sampling is a guardrail against "
            "treating any single completion as ground truth. "
            f"{len(run.accepted)} of those attempt(s) passed schema validation and are shown "
            f"below, numbered in the order they were accepted; {len(run.rejected)} were rejected "
            "(malformed JSON, a missing rating, a denylist match, etc.) -- see the Conversation "
            "Log tab for every rejected attempt and why.\n",
        ]
        for i, result in enumerate(run.accepted):
            sample_path_json = d / "samples" / f"sample_{i:02d}.json"
            sample_path_md = d / "samples" / f"sample_{i:02d}.md"
            sample_path_json.write_text(json.dumps(result.payload, indent=2), encoding="utf-8")
            reasoning = result.payload.get("reasoning", "(no reasoning field returned)")
            thinking = _extract_thinking(run.accepted_raw[i]) if i < len(run.accepted_raw) else None
            sample_path_md.write_text(
                f"# Sample {i + 1} of {len(run.accepted)}\n\n"
                f"- Best: {result.payload.get('best')}\n"
                f"- Worst: {result.payload.get('worst')}\n\n"
                + (f"## Full reasoning trace (model's own \"thinking\")\n\n{thinking}\n\n" if thinking else "")
                + f"## Stated reasoning (submitted with the answer)\n\n{reasoning}\n",
                encoding="utf-8",
            )
            thoughts_lines.append(f"## Sample {i + 1} of {len(run.accepted)} -- Best: {result.payload.get('best')}, Worst: {result.payload.get('worst')}\n")
            if thinking:
                thoughts_lines.append(f"**Full reasoning trace (model's own \"thinking\"):**\n\n{thinking}\n")
            thoughts_lines.append(f"**Stated reasoning (submitted with the answer):**\n\n{reasoning}\n")
        (d / "thoughts.md").write_text("\n".join(thoughts_lines), encoding="utf-8")

        result_summary = {
            "agent_id": agent_id,
            "accepted_count": len(run.accepted),
            "rejected_count": len(run.rejected),
            "flagged_low_agreement": run.flagged_low_agreement,
            "accepted_payloads": [r.payload for r in run.accepted],
        }
        (d / "result.json").write_text(json.dumps(result_summary, indent=2), encoding="utf-8")

        if card is not None and instrument_params is not None:
            (d / "filled_survey.md").write_text(
                _render_filled_survey(card, instrument_params, run), encoding="utf-8"
            )

    def write_report(self, markdown: str) -> Path:
        path = self.report_dir / "report.md"
        path.write_text(markdown, encoding="utf-8")
        return path

    def write_combined_results(self, data: Dict[str, Any]) -> Path:
        path = self.report_dir / "combined_results.json"
        path.write_text(json.dumps(data, indent=2, default=_json_default), encoding="utf-8")
        return path


def _render_filled_survey(card: AgentCard, instrument_params: Dict[str, Any], run: GuardedRun) -> str:
    """A single, human-readable rendering of this agent's completed survey:
    what it was, in one file, without needing samples/*.json or
    conversation.jsonl open side by side."""
    codes: List[str] = instrument_params.get("dimensions", [])
    labels: Dict[str, str] = instrument_params.get("dimension_labels", {})

    lines = [
        f"# Filled survey: {card.display_name or card.agent_id}\n",
        f"- Agent ID: `{card.agent_id}`",
        f"- Role / expertise: {card.role}" + (f" -- {card.expertise}" if card.expertise else ""),
        f"- Model: {card.model.provider}/{card.model.name}",
        f"- DID: `{card.did.id}`",
        f"- RAG: {'enabled, corpus ' + card.rag.corpus_path if card.rag.enabled else 'disabled'}",
        f"- Samples accepted: {len(run.accepted)} (requested: {card.sampling.repeats} independent attempts)\n",
    ]

    if run.accepted:
        lines.append("## Summary\n")
        lines.append("| Sample | Best | Worst |")
        lines.append("|---|---|---|")
        for i, result in enumerate(run.accepted):
            p = result.payload
            lines.append(f"| {i} | {p.get('best')} | {p.get('worst')} |")
        lines.append("")

    for i, result in enumerate(run.accepted):
        p = result.payload
        best, worst = p.get("best"), p.get("worst")
        lines.append(f"## Sample {i}\n")
        lines.append(f"**Best:** {best} ({labels.get(best, best)})  ")
        lines.append(f"**Worst:** {worst} ({labels.get(worst, worst)})\n")

        lines.append("### Best-to-Others\n")
        lines.append("| Criterion | Rating |")
        lines.append("|---|---|")
        for code in codes:
            lines.append(f"| {code} ({labels.get(code, code)}) | {p.get('best_to_others', {}).get(code, '-')} |")
        lines.append("")

        lines.append("### Others-to-Worst\n")
        lines.append("| Criterion | Rating |")
        lines.append("|---|---|")
        for code in codes:
            lines.append(f"| {code} ({labels.get(code, code)}) | {p.get('others_to_worst', {}).get(code, '-')} |")
        lines.append("")

        lines.append("### Reasoning\n")
        lines.append(p.get("reasoning", "(no reasoning field returned)") + "\n")

    if not run.accepted:
        lines.append("_No sample passed the guardrails; see conversation.jsonl for what was rejected and why._\n")

    return "\n".join(lines)


def _extract_thinking(response: ProviderResponse) -> str | None:
    """Some models (Ollama's deepseek-r1, gemma4, etc.) return their internal
    chain-of-thought in a separate `message.thinking` field, distinct from the
    final answer in `message.content`/`response.text`. Surface it when
    present so a reviewer can see the model's actual reasoning process, not
    just the 1-3 sentence summary it was asked to submit alongside its
    answer. Returns None for providers/responses that don't have this field
    (nothing is invented)."""
    thinking = (response.raw or {}).get("message", {}).get("thinking")
    return thinking.strip() if isinstance(thinking, str) and thinking.strip() else None


def _response_dict(response: ProviderResponse) -> Dict[str, Any]:
    return {"text": response.text, "model": response.model, "finish_reason": response.finish_reason, "raw": response.raw}


def _json_default(obj: Any) -> Any:
    if hasattr(obj, "tolist"):
        return obj.tolist()
    return str(obj)
