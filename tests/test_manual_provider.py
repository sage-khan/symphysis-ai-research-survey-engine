import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentic_survey.providers import manual_provider as manual_provider_module
from agentic_survey.providers.manual_provider import ManualProvider, ManualResponsePending

MESSAGES = [{"role": "system", "content": "You are a test agent."}, {"role": "user", "content": "Do the task."}]


@pytest.fixture(autouse=True)
def _reset_call_counters():
    # The per-directory call counter is module-level state that, in real
    # usage, naturally resets between CLI invocations (fresh process). Tests
    # run in one process, so reset it explicitly to keep tests independent
    # and to simulate "the next CLI run" within a single test.
    manual_provider_module._call_counters.clear()
    yield
    manual_provider_module._call_counters.clear()


def test_first_call_writes_prompt_and_raises_pending(tmp_path):
    provider = ManualProvider()
    manual_dir = tmp_path / "manual_input"

    with pytest.raises(ManualResponsePending):
        provider.complete(MESSAGES, model="gemini-2.5-pro", temperature=0.7, max_tokens=1024, manual_dir=str(manual_dir))

    prompt_path = manual_dir / "prompt_00.md"
    assert prompt_path.exists()
    assert "Do the task." in prompt_path.read_text()
    assert not (manual_dir / "response_00.txt").exists()


def test_second_call_after_pasting_response_succeeds(tmp_path):
    provider = ManualProvider()
    manual_dir = tmp_path / "manual_input"

    with pytest.raises(ManualResponsePending):
        provider.complete(MESSAGES, model="gemini-2.5-pro", temperature=0.7, max_tokens=1024, manual_dir=str(manual_dir))

    (manual_dir / "response_00.txt").write_text('{"best": "PT", "worst": "C"}', encoding="utf-8")

    # Simulate the human re-running the CLI (a fresh process) after pasting
    # the response, rather than a second call within the same run.
    manual_provider_module._call_counters.clear()

    result = provider.complete(MESSAGES, model="gemini-2.5-pro", temperature=0.7, max_tokens=1024, manual_dir=str(manual_dir))
    assert result.text == '{"best": "PT", "worst": "C"}'
    assert result.finish_reason == "manual"


def test_repeated_calls_advance_to_next_index(tmp_path):
    """Two sequential complete() calls in one process (as run_with_guardrails
    makes for repeats=2) must consume index 0 then move to index 1, not
    re-ask index 0 or skip straight past an already-answered one."""
    provider = ManualProvider()
    manual_dir = tmp_path / "manual_input"

    manual_dir.mkdir(parents=True)
    (manual_dir / "prompt_00.md").write_text("p0", encoding="utf-8")
    (manual_dir / "response_00.txt").write_text("r0", encoding="utf-8")

    first = provider.complete(MESSAGES, model="gemini-2.5-pro", temperature=0.7, max_tokens=1024, manual_dir=str(manual_dir))
    assert first.text == "r0"

    with pytest.raises(ManualResponsePending):
        provider.complete(MESSAGES, model="gemini-2.5-pro", temperature=0.7, max_tokens=1024, manual_dir=str(manual_dir))

    assert (manual_dir / "prompt_01.md").exists()
    assert not (manual_dir / "response_01.txt").exists()


def test_missing_manual_dir_kwarg_raises_provider_error():
    from agentic_survey.providers.base import ProviderError

    provider = ManualProvider()
    with pytest.raises(ProviderError):
        provider.complete(MESSAGES, model="gemini-2.5-pro", temperature=0.7, max_tokens=1024)
