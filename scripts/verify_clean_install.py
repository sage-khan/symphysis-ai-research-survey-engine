"""Verify the packaged `symphysis` distribution actually works installed
standalone: a full survey, end to end, using ONLY the installed package,
run from outside this repo's checkout (no PYTHONPATH=src, no repo config/
directory on disk). This is the concrete difference between "works when
cloned" and "works when installed" that docs/plan/packaging-plan.md calls
out as the thing to verify before ever cutting a release.

Usage: build the package (`python -m build`), install the wheel into a
fresh virtualenv, then run this script with that virtualenv's Python,
from any working directory:

    python -m venv /tmp/clean-install
    /tmp/clean-install/bin/pip install dist/*.whl
    /tmp/clean-install/bin/python scripts/verify_clean_install.py

Exits non-zero (via the assertion) on failure, so it can run unattended in
CI (see the "Package" job in .github/workflows/ci-cd.yml).
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import yaml

from symphysis.agent_card import GuardrailsSpec, ModelSpec, PermissionsSpec, RagSpec, SamplingSpec, new_card
from symphysis.config import load_survey_config
from symphysis.orchestrator import run_survey

DIMENSIONS = ["Q", "PT", "V", "IC", "L", "C"]


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        survey_dir = tmp_path / "clean-install-smoke-test"
        (survey_dir / "agents").mkdir(parents=True)
        survey_yaml = {
            "id": "clean-install-smoke-test",
            "title": "Clean install smoke test",
            "instrument": "bwm",
            "instrument_params": {"dimensions": DIMENSIONS, "dimension_labels": {}},
            "weighting": {},
        }
        (survey_dir / "survey.yaml").write_text(yaml.dump(survey_yaml), encoding="utf-8")

        prompt_template = tmp_path / "system_prompt.txt"
        prompt_template.write_text("Role: {role}\n{role_description}\n", encoding="utf-8")

        card = new_card(
            agent_id="clean-install-smoke-agent",
            role="Reviewer",
            role_description="A reviewer.",
            system_prompt_template=str(prompt_template),
            model=ModelSpec(provider="manual", name="gemini-2.5-pro"),
            rag=RagSpec(enabled=False),
            sampling=SamplingSpec(repeats=1, max_retries_on_malformed=0),
            permissions=PermissionsSpec(allowed_providers=["manual"]),
            guardrails=GuardrailsSpec(),
            did_seed="clean-install-smoke-test-seed",
        )
        card.write(survey_dir / "agents" / "clean-install-smoke-agent.json")

        manual_dir = survey_dir / "agents" / "clean-install-smoke-agent" / "manual_input"
        manual_dir.mkdir(parents=True)
        (manual_dir / "prompt_00.md").write_text("prompt", encoding="utf-8")
        (manual_dir / "response_00.txt").write_text(
            json.dumps(
                {
                    "best": "PT",
                    "worst": "C",
                    "best_to_others": {"Q": 2, "PT": 1, "V": 3, "IC": 4, "L": 2, "C": 8},
                    "others_to_worst": {"Q": 4, "PT": 8, "V": 5, "IC": 3, "L": 4, "C": 1},
                    "reasoning": "test",
                }
            ),
            encoding="utf-8",
        )

        survey = load_survey_config(survey_dir)
        result = run_survey(survey)
        assert result["agent_panel"]["num_agents"] == 1, result

        report_path = survey_dir / "report" / "report.md"
        assert report_path.exists() and report_path.stat().st_size > 0, "report.md missing or empty"

        print(f"Clean-install smoke test PASSED: report at {report_path} ({report_path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
