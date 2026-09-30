"""Collect every currently-pending manual_input/prompt_NN*.md file across one
or more survey-level folders into ONE ordered chain document: work through it
top to bottom, pasting each block into a NEW chat with the model named in the
block header (a fresh chat per block, not one long conversation -- see the
"why a fresh chat" note this script prints), then paste that reply under the
block's ANSWER: marker, in the same file, in place.

Once you've filled in every ANSWER: marker in the produced file, hand it to
relay_chain_ingest.py, which splits your pasted answers back out into the
exact response_NN.txt files symphysis's ManualProvider is waiting on, then
you re-run `symphysis run <survey_dir>` per level to advance the pipeline
(next repeat, or done) and re-run this script to build the next chain file.

Usage:
    cd /path/to/symphysis-ai-research-survey-engine
    PYTHONPATH=src python3 -m symphysis.cli run surveys/<parent>-L1   # writes this round's prompt files
    python3 scripts/relay_chain_build.py surveys/<parent>-L1 [surveys/<parent>-L2 ...] \
        --out /tmp/relay_chain_L1.md

Pass one or more survey-level directories built by
build_trustrouter_manual_relay_full_panel_surveys.py. Only agents/samples
with a prompt file but no matching response file yet are included -- already
-answered samples are skipped automatically, so re-running this after a
partial fill only asks for what's actually still missing.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

PROMPT_RE = re.compile(r"^prompt_(\d+)(?:_r(\d+))?\.md$")


def _repeats_for(agent_dir: Path) -> int:
    card_path = agent_dir / "card.json"
    try:
        card = json.loads(card_path.read_text(encoding="utf-8"))
        return int(card["sampling"]["repeats"])
    except Exception:
        return 1


def find_pending(survey_dir: Path) -> list[tuple[Path, str, int, int]]:
    """Returns (prompt_path, agent_id, sample_idx, attempt) for every prompt
    file in this survey that has no matching response file yet."""
    pending = []
    agents_dir = survey_dir / "agents"
    for agent_dir in sorted(agents_dir.glob("*")):
        manual_dir = agent_dir / "manual_input"
        if not manual_dir.is_dir():
            continue
        for prompt_path in sorted(manual_dir.glob("prompt_*.md")):
            m = PROMPT_RE.match(prompt_path.name)
            if not m:
                continue
            sample_idx = int(m.group(1))
            attempt = int(m.group(2)) if m.group(2) else 0
            suffix = f"_r{attempt}" if attempt else ""
            response_path = manual_dir / f"response_{sample_idx:02d}{suffix}.txt"
            if not response_path.exists():
                pending.append((prompt_path, agent_dir.name, sample_idx, attempt))
    return pending


def build_chain(survey_dirs: list[Path], out_path: Path) -> None:
    all_blocks: list[tuple[Path, str, str, int, int]] = []  # (response_path, survey_id, agent_id, sample_idx, attempt)
    for survey_dir in survey_dirs:
        survey_id = survey_dir.name
        for prompt_path, agent_id, sample_idx, attempt in find_pending(survey_dir):
            suffix = f"_r{attempt}" if attempt else ""
            response_path = prompt_path.parent / f"response_{sample_idx:02d}{suffix}.txt"
            all_blocks.append((response_path, survey_id, agent_id, sample_idx, attempt, prompt_path))

    if not all_blocks:
        print("Nothing pending -- every discovered prompt file already has a matching response file.")
        print("Re-run `symphysis run <survey_dir>` first if you expect a new round to exist.")
        return

    lines = [
        "# TrustRouter Manual Relay -- prompt chain",
        "",
        f"{len(all_blocks)} block(s) below, each one full model turn. **Use a fresh, new chat "
        "for every block** (not one continuous conversation): every other condition in this "
        "panel (local SLMs, Claude Haiku/Sonnet, the Gemini API) answers each level/sample as an "
        "independent judgement with no memory of the others, and this survey's own rulefile says "
        "so explicitly (\"Each level runs as its own independent, single-comparison-set survey\"). "
        "Answering inside one long thread would let each answer anchor on the previous one's "
        "reasoning, which no other condition in this dataset does -- it would not be a fair "
        "comparison point.",
        "",
        "For each block: copy everything between the COPY markers into a new chat with the named "
        "model, wait for its full reply, then paste that reply verbatim -- nothing added, nothing "
        "trimmed -- directly under the `ANSWER:` line, replacing the placeholder text. Leave the "
        "`<!-- RELAY-BLOCK -->` marker line untouched; the ingest script keys off it.",
        "",
        "---",
        "",
    ]

    for i, (response_path, survey_id, agent_id, sample_idx, attempt, prompt_path) in enumerate(all_blocks, 1):
        prompt_text = prompt_path.read_text(encoding="utf-8")
        # Strip the manual_provider.py boilerplate header line; the chain
        # document's own instructions replace it.
        prompt_text = re.sub(
            r"^# Paste this into the model's chat UI.*\n+", "", prompt_text, count=1
        )
        retry_note = f" (repair retry {attempt})" if attempt else ""
        total_repeats = _repeats_for(prompt_path.parent.parent)
        lines.append(
            f'<!-- RELAY-BLOCK path="{response_path.as_posix()}" -->'
        )
        lines.append(f"## [{i}/{len(all_blocks)}] {agent_id} -- {survey_id} -- sample {sample_idx + 1} of {total_repeats}{retry_note}")
        lines.append("")
        lines.append(">>> COPY EVERYTHING BELOW THIS LINE, INTO A NEW CHAT, UP TO THE NEXT MARKER <<<")
        lines.append("")
        lines.append(prompt_text.rstrip())
        lines.append("")
        lines.append(">>> END OF TEXT TO COPY <<<")
        lines.append("")
        lines.append("ANSWER:")
        lines.append("(paste the model's raw reply here, nothing else, then move to the next block)")
        lines.append("")
        lines.append("---")
        lines.append("")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {len(all_blocks)} pending block(s) to {out_path}")
    print("Work through it top to bottom, then run relay_chain_ingest.py on the filled-in file.")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("survey_dirs", nargs="+", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    build_chain([d.resolve() for d in args.survey_dirs], args.out.resolve())


if __name__ == "__main__":
    main()
