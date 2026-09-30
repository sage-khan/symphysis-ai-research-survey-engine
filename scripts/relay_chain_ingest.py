"""Split a filled-in relay-chain document (produced by relay_chain_build.py,
then hand-completed by pasting each model's reply under its ANSWER: marker)
back out into the individual response_NN.txt files symphysis's ManualProvider
is waiting on.

After this, re-run `symphysis run <survey_dir>` for each affected survey to
advance the pipeline (resolves this round's samples; writes the next round's
prompt files if repeats aren't exhausted yet, exactly like every other
provider in this project).

Usage:
    python3 scripts/relay_chain_ingest.py /tmp/relay_chain_L1.md
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

BLOCK_RE = re.compile(r'<!-- RELAY-BLOCK path="([^"]+)" -->')
PLACEHOLDER = "(paste the model's raw reply here, nothing else, then move to the next block)"


def ingest(chain_path: Path) -> None:
    text = chain_path.read_text(encoding="utf-8")
    matches = list(BLOCK_RE.finditer(text))
    if not matches:
        print(f"No RELAY-BLOCK markers found in {chain_path} -- nothing to ingest.")
        return

    written, skipped, missing_target_dir = 0, 0, 0
    for i, m in enumerate(matches):
        response_path = Path(m.group(1))
        block_start = m.end()
        block_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        block_text = text[block_start:block_end]

        answer_idx = block_text.find("ANSWER:")
        if answer_idx == -1:
            print(f"  [skip] {response_path}: no ANSWER: marker found in its block")
            skipped += 1
            continue

        answer_text = block_text[answer_idx + len("ANSWER:"):]
        # Drop the block's own trailing "---" separator and any blank lines
        # around it, without touching internal content.
        answer_text = re.sub(r"\n-{3,}\s*$", "", answer_text)
        answer_text = answer_text.strip("\n")
        answer_text = answer_text.strip()

        if not answer_text or answer_text == PLACEHOLDER:
            print(f"  [skip] {response_path}: still has the placeholder / is empty (not answered yet)")
            skipped += 1
            continue

        if not response_path.parent.exists():
            print(f"  [error] {response_path}: parent directory does not exist, skipping")
            missing_target_dir += 1
            continue

        response_path.write_text(answer_text, encoding="utf-8")
        written += 1
        print(f"  [ok] wrote {len(answer_text)} chars -> {response_path}")

    print(f"\n{written} response file(s) written, {skipped} still pending/unanswered"
          + (f", {missing_target_dir} target-directory error(s)" if missing_target_dir else "") + ".")
    if written:
        print("Now re-run `symphysis run <survey_dir>` for each affected survey to advance the pipeline.")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("chain_file", type=Path)
    args = ap.parse_args()
    if not args.chain_file.exists():
        print(f"No such file: {args.chain_file}", file=sys.stderr)
        raise SystemExit(1)
    ingest(args.chain_file.resolve())


if __name__ == "__main__":
    main()
