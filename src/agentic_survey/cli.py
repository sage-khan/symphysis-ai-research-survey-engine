"""Command-line entrypoint.

    python -m agentic_survey.cli run <survey-dir>
    python -m agentic_survey.cli new <survey-dir> --title "..." --id ...
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import ConfigError, load_survey_config
from .orchestrator import run_survey


def cmd_run(args: argparse.Namespace) -> int:
    survey_dir = Path(args.survey_dir).resolve()
    try:
        survey = load_survey_config(survey_dir)
    except ConfigError as exc:
        print(f"Config error: {exc}", file=sys.stderr)
        return 1

    result = run_survey(survey)
    print(f"Survey '{survey.title}' complete.")
    print(f"Agents contributing: {result['agent_panel']['num_agents']}")
    print(f"Report: {survey_dir / 'report' / 'report.md'}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agentic-survey")
    sub = parser.add_subparsers(dest="command", required=True)

    run_p = sub.add_parser("run", help="Run every agent in a survey project folder and produce the report")
    run_p.add_argument("survey_dir", help="Path to the survey project folder (must contain survey.yaml and agents/)")
    run_p.set_defaults(func=cmd_run)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
