import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from typer.testing import CliRunner

from symphysis.cli import app

runner = CliRunner()


def _seed_manual_response(survey_dir: Path, agent_id: str) -> None:
    manual_dir = survey_dir / "agents" / agent_id / "manual_input"
    manual_dir.mkdir(parents=True, exist_ok=True)
    (manual_dir / "prompt_00.md").write_text("prompt", encoding="utf-8")
    (manual_dir / "response_00.txt").write_text(
        json.dumps({
            "best": "PT", "worst": "C",
            "best_to_others": {"Q": 2, "PT": 1, "V": 3, "IC": 4, "L": 2, "C": 8},
            "others_to_worst": {"Q": 4, "PT": 8, "V": 5, "IC": 3, "L": 4, "C": 1},
            "reasoning": "cli test",
        }),
        encoding="utf-8",
    )


def test_new_scaffolds_a_survey_yaml_and_agents_dir(tmp_path):
    survey_dir = tmp_path / "cli-new-test"
    result = runner.invoke(app, ["new", "cli-new-test", "--dimensions", "Q,PT,V", "--output", str(survey_dir)])
    assert result.exit_code == 0, result.output
    assert (survey_dir / "survey.yaml").exists()
    assert (survey_dir / "agents").is_dir()


def test_new_refuses_to_overwrite_without_force(tmp_path):
    survey_dir = tmp_path / "cli-new-overwrite-test"
    runner.invoke(app, ["new", "cli-new-overwrite-test", "--dimensions", "Q,PT,V", "--output", str(survey_dir)])
    result = runner.invoke(app, ["new", "cli-new-overwrite-test", "--dimensions", "Q,PT,V", "--output", str(survey_dir)])
    assert result.exit_code == 1
    assert "already exists" in result.output


def test_new_requires_dimensions_for_bwm(tmp_path):
    result = runner.invoke(app, ["new", "no-dims", "--output", str(tmp_path / "no-dims")])
    assert result.exit_code == 1
    assert "--dimensions is required" in result.output


def test_new_rejects_an_unknown_instrument(tmp_path):
    result = runner.invoke(app, ["new", "bad-instrument", "--instrument", "nonsense", "--output", str(tmp_path / "x")])
    assert result.exit_code == 1
    assert "Unknown instrument" in result.output


def test_add_agent_creates_a_card_with_bundled_prompt_template(tmp_path):
    survey_dir = tmp_path / "cli-add-agent-test"
    runner.invoke(app, ["new", "cli-add-agent-test", "--dimensions", "Q,PT,V", "--output", str(survey_dir)])
    result = runner.invoke(
        app,
        ["add-agent", str(survey_dir), "--agent-id", "test-agent", "--role", "Data Engineer",
         "--provider", "manual", "--model", "gemini-2.5-pro"],
    )
    assert result.exit_code == 0, result.output
    card_path = survey_dir / "agents" / "test-agent.json"
    assert card_path.exists()
    card = json.loads(card_path.read_text(encoding="utf-8"))
    assert card["role"] == "Data Engineer"
    assert card["model"]["provider"] == "manual"
    assert Path(card["system_prompt_template"]).exists()


def test_add_agent_refuses_a_duplicate_agent_id(tmp_path):
    survey_dir = tmp_path / "cli-add-agent-dup-test"
    runner.invoke(app, ["new", "cli-add-agent-dup-test", "--dimensions", "Q,PT,V", "--output", str(survey_dir)])
    runner.invoke(
        app,
        ["add-agent", str(survey_dir), "--agent-id", "dup-agent", "--role", "Reviewer",
         "--provider", "manual", "--model", "gemini-2.5-pro"],
    )
    result = runner.invoke(
        app,
        ["add-agent", str(survey_dir), "--agent-id", "dup-agent", "--role", "Reviewer",
         "--provider", "manual", "--model", "gemini-2.5-pro"],
    )
    assert result.exit_code == 1
    assert "already has an agent" in result.output


def test_add_agent_from_library_copies_the_card(tmp_path):
    library_root = tmp_path / "library"
    library_root.mkdir()
    survey_dir = tmp_path / "cli-add-agent-lib-test"
    runner.invoke(app, ["new", "cli-add-agent-lib-test", "--dimensions", "Q,PT,V", "--output", str(survey_dir)])
    # Seed a minimal library card via the same add-agent path, then copy it
    # from a *different* survey into this one, exactly like --from-library.
    other_survey = tmp_path / "other-survey"
    runner.invoke(app, ["new", "other-survey", "--dimensions", "Q,PT,V", "--output", str(other_survey)])
    runner.invoke(
        app,
        ["add-agent", str(other_survey), "--agent-id", "lib-agent", "--role", "Reviewer",
         "--provider", "manual", "--model", "gemini-2.5-pro"],
    )
    (library_root / "lib-agent.json").write_text(
        (other_survey / "agents" / "lib-agent.json").read_text(encoding="utf-8"), encoding="utf-8"
    )

    result = runner.invoke(
        app, ["add-agent", str(survey_dir), "--from-library", "lib-agent", "--library-root", str(library_root)]
    )
    assert result.exit_code == 0, result.output
    assert (survey_dir / "agents" / "lib-agent.json").exists()


def test_add_agent_from_library_reports_a_missing_agent_clearly(tmp_path):
    library_root = tmp_path / "empty-library"
    library_root.mkdir()
    survey_dir = tmp_path / "cli-add-agent-missing-lib-test"
    runner.invoke(app, ["new", "cli-add-agent-missing-lib-test", "--dimensions", "Q,PT,V", "--output", str(survey_dir)])
    result = runner.invoke(
        app, ["add-agent", str(survey_dir), "--from-library", "no-such-agent", "--library-root", str(library_root)]
    )
    assert result.exit_code == 1
    assert "No library agent" in result.output


def test_fix_survey_reports_clean_and_writes_a_report_file(tmp_path):
    survey_dir = tmp_path / "cli-fix-survey-test"
    runner.invoke(app, ["new", "cli-fix-survey-test", "--dimensions", "Q,PT,V", "--output", str(survey_dir)])
    runner.invoke(
        app,
        ["add-agent", str(survey_dir), "--agent-id", "a1", "--role", "Reviewer",
         "--provider", "manual", "--model", "gemini-2.5-pro"],
    )
    result = runner.invoke(app, ["fix-survey", str(survey_dir)])
    assert result.exit_code == 0, result.output
    assert "No problems found" in result.output
    assert (survey_dir / "fix-report.md").exists()


def test_fix_survey_exits_nonzero_on_a_dangling_rag_path(tmp_path):
    survey_dir = tmp_path / "cli-fix-survey-bad-test"
    runner.invoke(app, ["new", "cli-fix-survey-bad-test", "--dimensions", "Q,PT,V", "--output", str(survey_dir)])
    runner.invoke(
        app,
        ["add-agent", str(survey_dir), "--agent-id", "a1", "--role", "Reviewer",
         "--provider", "manual", "--model", "gemini-2.5-pro"],
    )
    card_path = survey_dir / "agents" / "a1.json"
    card = json.loads(card_path.read_text(encoding="utf-8"))
    card["rag"]["enabled"] = True
    card["rag"]["corpus_path"] = str(tmp_path / "no-such-corpus")
    card_path.write_text(json.dumps(card), encoding="utf-8")

    result = runner.invoke(app, ["fix-survey", str(survey_dir)])
    assert result.exit_code == 1
    assert "does not exist as a directory" in result.output


def test_run_then_report_round_trip(tmp_path):
    survey_dir = tmp_path / "cli-run-report-test"
    runner.invoke(app, ["new", "cli-run-report-test", "--dimensions", "Q,PT,V,IC,L,C", "--output", str(survey_dir)])
    runner.invoke(
        app,
        ["add-agent", str(survey_dir), "--agent-id", "a1", "--role", "Reviewer",
         "--provider", "manual", "--model", "gemini-2.5-pro"],
    )
    card_path = survey_dir / "agents" / "a1.json"
    card = json.loads(card_path.read_text(encoding="utf-8"))
    card["sampling"]["repeats"] = 1
    card_path.write_text(json.dumps(card), encoding="utf-8")
    _seed_manual_response(survey_dir, "a1")

    run_result = runner.invoke(app, ["run", str(survey_dir)])
    assert run_result.exit_code == 0, run_result.output
    assert (survey_dir / "report" / "report.md").exists()

    report_result = runner.invoke(app, ["report", str(survey_dir)])
    assert report_result.exit_code == 0, report_result.output
    assert "Agent-samples replayed: 1" in report_result.output


def test_report_fails_clearly_with_no_samples_yet(tmp_path):
    survey_dir = tmp_path / "cli-report-empty-test"
    runner.invoke(app, ["new", "cli-report-empty-test", "--dimensions", "Q,PT,V", "--output", str(survey_dir)])
    runner.invoke(
        app,
        ["add-agent", str(survey_dir), "--agent-id", "a1", "--role", "Reviewer",
         "--provider", "manual", "--model", "gemini-2.5-pro"],
    )
    result = runner.invoke(app, ["report", str(survey_dir)])
    assert result.exit_code == 1
    assert "nothing to solve" in result.output


def test_run_checks_provider_availability_first_and_prints_it(tmp_path):
    survey_dir = tmp_path / "cli-preflight-manual-test"
    runner.invoke(app, ["new", "cli-preflight-manual-test", "--dimensions", "Q,PT,V,IC,L,C", "--output", str(survey_dir)])
    runner.invoke(
        app,
        ["add-agent", str(survey_dir), "--agent-id", "a1", "--role", "Reviewer",
         "--provider", "manual", "--model", "gemini-2.5-pro"],
    )
    card_path = survey_dir / "agents" / "a1.json"
    card = json.loads(card_path.read_text(encoding="utf-8"))
    card["sampling"]["repeats"] = 1
    card_path.write_text(json.dumps(card), encoding="utf-8")
    _seed_manual_response(survey_dir, "a1")

    result = runner.invoke(app, ["run", str(survey_dir)])
    assert result.exit_code == 0, result.output
    lines = result.output.splitlines()
    assert lines[0] == "Checking LLM provider availability..."
    assert any("manual" in line and "[ok]" in line for line in lines)


def test_run_aborts_before_running_when_a_provider_preflight_fails(tmp_path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    survey_dir = tmp_path / "cli-preflight-fail-test"
    runner.invoke(app, ["new", "cli-preflight-fail-test", "--dimensions", "Q,PT,V", "--output", str(survey_dir)])
    runner.invoke(
        app,
        ["add-agent", str(survey_dir), "--agent-id", "a1", "--role", "Reviewer",
         "--provider", "anthropic", "--model", "claude-opus-5"],
    )
    result = runner.invoke(app, ["run", str(survey_dir)])
    assert result.exit_code == 1
    assert "[FAIL]" in result.output
    assert "Aborting before running any agent" in result.output
    # Confirm it genuinely aborted before attempting anything: no report
    # was ever written.
    assert not (survey_dir / "report" / "report.md").exists()


def test_run_ignore_preflight_failures_runs_anyway(tmp_path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    survey_dir = tmp_path / "cli-preflight-ignore-test"
    runner.invoke(app, ["new", "cli-preflight-ignore-test", "--dimensions", "Q,PT,V", "--output", str(survey_dir)])
    runner.invoke(
        app,
        ["add-agent", str(survey_dir), "--agent-id", "a1", "--role", "Reviewer",
         "--provider", "anthropic", "--model", "claude-opus-5"],
    )
    result = runner.invoke(app, ["run", str(survey_dir), "--ignore-preflight-failures"])
    # Still fails overall (the anthropic agent has no key and gets skipped,
    # so nothing accepted, per orchestrator's own "nothing to solve"
    # RuntimeError), but it got PAST the preflight abort this time.
    assert "Aborting before running any agent" not in result.output
    assert "[FAIL]" in result.output
