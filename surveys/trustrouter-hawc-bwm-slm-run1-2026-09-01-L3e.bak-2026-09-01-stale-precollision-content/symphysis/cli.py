"""The `symphysis` command-line entry point.

    symphysis run <survey-dir>
    symphysis new <survey-id> --dimensions Q,PT,V,IC,L,C
    symphysis add-agent <survey-dir> --from-library <agent-id>
    symphysis add-agent <survey-dir> --agent-id ... --role ... --provider ollama --model qwen2.5:14b
    symphysis fix-survey <survey-dir>
    symphysis report <survey-dir>

Every subcommand operates on a survey project folder (a directory holding
survey.yaml and agents/*.json, see storage.py's module docstring for the
full on-disk layout) exactly as the web UI does; this CLI is a first-class
alternative to the web UI, not a stripped-down fallback for it.
"""

from __future__ import annotations

import sys
from importlib import resources
from pathlib import Path
from typing import Annotated, List, Optional

import typer
import yaml

from .agent_card import AgentCardError, GuardrailsSpec, ModelSpec, PermissionsSpec, RagSpec, SamplingSpec, load_card, new_card
from .config import ConfigError, SurveyConfig, load_survey_config
from .orchestrator import regenerate_report, run_survey
from .preflight import check_survey_providers
from .survey_checks import fix_survey

app = typer.Typer(
    name="symphysis",
    help="Config-driven agent panels for expert-elicitation surveys (BWM, AHP, hierarchical variants).",
    no_args_is_help=True,
    add_completion=True,
)

KNOWN_INSTRUMENTS = ["bwm", "ahp", "hierarchical_bwm"]


def _err(message: str) -> None:
    typer.secho(message, fg=typer.colors.RED, err=True)


def _bundled_prompt_template_text() -> str:
    return resources.files("symphysis").joinpath("_bundled_prompts", "expert_panel_system.txt").read_text(
        encoding="utf-8"
    )


def _run_preflight(survey: SurveyConfig) -> bool:
    """Checked, and printed, before anything else: is every provider this
    survey's agents actually need reachable right now? A dead Ollama
    instance or an unset hosted-provider API key otherwise only surfaces
    deep into a run (after RAG indexing, QA prechecks, however many
    samples), wasting real time on an error that was knowable up front.
    Returns whether every provider passed."""
    typer.echo("Checking LLM provider availability...")
    statuses = check_survey_providers(survey)
    if not statuses:
        _err("  No agent card could be loaded; nothing to check.")
        return False

    all_ok = True
    for status in statuses:
        if status.ok:
            typer.secho(f"  [ok]   {status.provider}: {status.detail}", fg=typer.colors.GREEN)
        else:
            typer.secho(f"  [FAIL] {status.provider}: {status.detail}", fg=typer.colors.RED)
            all_ok = False
    return all_ok


@app.command()
def run(
    survey_dir: Annotated[Path, typer.Argument(help="Path to the survey project folder (survey.yaml + agents/).")],
    ignore_preflight_failures: Annotated[
        bool,
        typer.Option(
            "--ignore-preflight-failures",
            help="Run anyway even if a provider preflight check fails (agents on that provider are still "
            "individually skipped, as always; this only skips the upfront abort).",
        ),
    ] = False,
) -> None:
    """Run every agent in a survey project folder and produce the report."""
    survey_dir = survey_dir.resolve()
    try:
        survey = load_survey_config(survey_dir)
    except ConfigError as exc:
        _err(f"Config error: {exc}")
        raise typer.Exit(code=1)

    preflight_ok = _run_preflight(survey)
    if not preflight_ok and not ignore_preflight_failures:
        _err(
            "Aborting before running any agent: at least one required provider failed its preflight "
            "check (see above). Fix it, or pass --ignore-preflight-failures to run anyway (agents on "
            "a failing provider will simply be skipped, same as always)."
        )
        raise typer.Exit(code=1)

    try:
        result = run_survey(survey)
    except RuntimeError as exc:
        _err(str(exc))
        raise typer.Exit(code=1)

    typer.echo(f"Survey '{survey.title}' complete.")
    typer.echo(f"Agents contributing: {result['agent_panel']['num_agents']}")
    typer.echo(f"Report: {survey_dir / 'report' / 'report.md'}")


@app.command()
def new(
    survey_id: Annotated[str, typer.Argument(help="Short, filesystem-safe survey identifier.")],
    title: Annotated[Optional[str], typer.Option(help="Human-readable survey title. Defaults to survey_id.")] = None,
    instrument: Annotated[
        str, typer.Option(help=f"Instrument to use. One of: {', '.join(KNOWN_INSTRUMENTS)}.")
    ] = "bwm",
    dimensions: Annotated[
        Optional[str],
        typer.Option(help="Comma-separated criteria codes, e.g. Q,PT,V,IC,L,C. Required for bwm/ahp."),
    ] = None,
    output: Annotated[
        Optional[Path], typer.Option(help="Directory to scaffold the survey into. Defaults to ./<survey-id>.")
    ] = None,
    force: Annotated[bool, typer.Option(help="Overwrite an existing survey.yaml at the target location.")] = False,
) -> None:
    """Scaffold a new survey project folder: survey.yaml plus an empty
    agents/ directory. Add agents afterward with `symphysis add-agent`."""
    if instrument not in KNOWN_INSTRUMENTS:
        _err(f"Unknown instrument '{instrument}'. Known: {', '.join(KNOWN_INSTRUMENTS)}")
        raise typer.Exit(code=1)

    survey_dir = (output or Path(survey_id)).resolve()
    survey_yaml_path = survey_dir / "survey.yaml"
    if survey_yaml_path.exists() and not force:
        _err(f"{survey_yaml_path} already exists. Pass --force to overwrite.")
        raise typer.Exit(code=1)

    if instrument == "hierarchical_bwm":
        instrument_params = {
            "composite_formula": "<describe how your levels combine, e.g. 'Score = A x B'>",
            "levels": [
                {
                    "id": "L1",
                    "name": "<top-level factors>",
                    "description": "<what this level compares>",
                    "dimensions": ["<CODE1>", "<CODE2>"],
                    "dimension_labels": {"<CODE1>": "<label>", "<CODE2>": "<label>"},
                }
            ],
        }
        typer.echo(
            "hierarchical_bwm scaffolded with one placeholder root level. Edit survey.yaml's "
            "instrument_params.levels by hand to add your real levels (each with 'id', "
            "'dimensions', and, for every non-root level, 'parent_level'/'parent_criterion' "
            "pointing at its parent). Run `symphysis fix-survey` afterward to check the result."
        )
    else:
        codes = [c.strip() for c in dimensions.split(",")] if dimensions else []
        if not codes:
            _err(f"--dimensions is required for instrument '{instrument}', e.g. --dimensions Q,PT,V,IC,L,C")
            raise typer.Exit(code=1)
        instrument_params = {"dimensions": codes, "dimension_labels": {}}

    (survey_dir / "agents").mkdir(parents=True, exist_ok=True)
    survey_yaml_path.write_text(
        yaml.dump(
            {
                "id": survey_id,
                "title": title or survey_id,
                "instrument": instrument,
                "instrument_params": instrument_params,
                "weighting": {},
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    typer.echo(f"Scaffolded survey '{survey_id}' at {survey_dir}")
    typer.echo(f"Next: symphysis add-agent {survey_dir} --agent-id ... --role ... --provider ollama --model ...")


@app.command("add-agent")
def add_agent(
    survey_dir: Annotated[Path, typer.Argument(help="Path to the survey project folder.")],
    from_library: Annotated[
        Optional[str], typer.Option("--from-library", help="Copy an existing Agent Card by id from --library-root.")
    ] = None,
    library_root: Annotated[Path, typer.Option(help="Directory of reusable Agent Cards.")] = Path("agents_library"),
    agent_id: Annotated[Optional[str], typer.Option(help="New agent's id (required unless --from-library).")] = None,
    role: Annotated[Optional[str], typer.Option(help="Professional role, e.g. 'Data Engineer'.")] = None,
    role_description: Annotated[Optional[str], typer.Option(help="Narrative description of the role.")] = None,
    provider: Annotated[
        str, typer.Option(help="ollama, anthropic, openai, openrouter, groq, gemini, xai, manual.")
    ] = "ollama",
    model: Annotated[str, typer.Option(help="Model name, e.g. qwen2.5:14b.")] = "qwen2.5:14b",
    role_pack: Annotated[Optional[str], typer.Option(help="Id of a standard role knowledge pack, if any.")] = None,
    display_name: Annotated[Optional[str], typer.Option(help="Human-facing display name.")] = None,
) -> None:
    """Add an agent to a survey, either copied from the Agent Library
    (--from-library) or created fresh from the given flags."""
    survey_dir = survey_dir.resolve()
    survey_yaml_path = survey_dir / "survey.yaml"
    if not survey_yaml_path.exists():
        _err(f"No survey.yaml found at {survey_dir}. Run `symphysis new` first.")
        raise typer.Exit(code=1)

    agents_dir = survey_dir / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)

    if from_library:
        src_path = library_root.resolve() / f"{from_library}.json"
        if not src_path.exists():
            _err(f"No library agent '{from_library}' at {src_path}")
            raise typer.Exit(code=1)
        dest_path = agents_dir / f"{from_library}.json"
        if dest_path.exists():
            _err(f"Survey already has an agent '{from_library}' at {dest_path}")
            raise typer.Exit(code=1)
        try:
            card = load_card(src_path)
        except AgentCardError as exc:
            _err(f"Failed to load library card: {exc}")
            raise typer.Exit(code=1)
        card.write(dest_path)
        typer.echo(f"Added '{from_library}' (copied from {library_root}) to {agents_dir}")
        return

    if not agent_id or not role:
        _err("--agent-id and --role are required when not using --from-library.")
        raise typer.Exit(code=1)

    dest_path = agents_dir / f"{agent_id}.json"
    if dest_path.exists():
        _err(f"Survey already has an agent '{agent_id}' at {dest_path}")
        raise typer.Exit(code=1)

    # A freshly scaffolded card gets its own copy of the bundled default
    # system-prompt template, written as an ABSOLUTE path inside the survey
    # directory: unlike the hand-authored example cards shipped in this
    # repo (which use a repo-root-relative path and assume the process's
    # CWD is the repo root), a card generated here must keep working
    # regardless of what directory `symphysis run` is later invoked from,
    # including a survey folder that gets moved or shared standalone.
    template_path = survey_dir / "system_prompt.txt"
    if not template_path.exists():
        template_path.write_text(_bundled_prompt_template_text(), encoding="utf-8")

    instrument = "bwm"
    if any(agents_dir.glob("*.json")):
        try:
            instrument = load_survey_config(survey_dir).instrument
        except ConfigError:
            pass

    card = new_card(
        agent_id=agent_id,
        role=role,
        role_description=role_description or f"An expert in the role of {role}.",
        system_prompt_template=str(template_path),
        model=ModelSpec(provider=provider, name=model),
        instrument=instrument,
        rag=RagSpec(enabled=False),
        sampling=SamplingSpec(),
        permissions=PermissionsSpec(),
        guardrails=GuardrailsSpec(),
        role_pack=role_pack,
        display_name=display_name,
        did_seed=f"symphysis-cli-{survey_dir.name}",
    )
    card.write(dest_path)
    typer.echo(f"Added '{agent_id}' ({role}, {provider}/{model}) to {agents_dir}")


@app.command("fix-survey")
def fix_survey_cmd(
    survey_dir: Annotated[Path, typer.Argument(help="Path to the survey project folder.")],
    write_report: Annotated[
        bool, typer.Option("--write-report/--no-write-report", help="Also write fix-report.md into the survey folder.")
    ] = True,
) -> None:
    """Validate a survey's configuration (schema, instrument-params
    completeness, dangling RAG/role-pack/prompt-template references)
    without running it. Exits non-zero if any problem is found."""
    survey_dir = survey_dir.resolve()
    problems = fix_survey(survey_dir)

    if write_report:
        report_path = survey_dir / "fix-report.md"
        lines = [f"# fix-survey report: {survey_dir}\n"]
        if problems:
            lines.append(f"{len(problems)} problem(s) found:\n")
            lines.extend(f"- {p}" for p in problems)
        else:
            lines.append("No problems found.")
        report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    if not problems:
        typer.echo(f"No problems found in {survey_dir}")
        return

    _err(f"{len(problems)} problem(s) found in {survey_dir}:")
    for p in problems:
        _err(f"  - {p}")
    raise typer.Exit(code=1)


@app.command()
def report(
    survey_dir: Annotated[Path, typer.Argument(help="Path to the survey project folder.")],
) -> None:
    """Regenerate the report/charts from each agent's already-accepted
    samples on disk, without calling any provider. Useful after
    hand-correcting a malformed sample, without re-running the whole
    survey against live providers."""
    survey_dir = survey_dir.resolve()
    try:
        survey = load_survey_config(survey_dir)
    except ConfigError as exc:
        _err(f"Config error: {exc}")
        raise typer.Exit(code=1)

    try:
        result = regenerate_report(survey)
    except RuntimeError as exc:
        _err(str(exc))
        raise typer.Exit(code=1)

    typer.echo(f"Report regenerated for '{survey.title}'.")
    typer.echo(f"Agent-samples replayed: {result['agent_panel']['num_agents']}")
    typer.echo(f"Report: {survey_dir / 'report' / 'report.md'}")


def main(argv: Optional[List[str]] = None) -> int:
    try:
        app(args=argv, prog_name="symphysis")
    except SystemExit as exc:
        return exc.code or 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
