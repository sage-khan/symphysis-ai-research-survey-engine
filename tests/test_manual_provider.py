import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentic_survey.providers.base import ProviderError
from agentic_survey.providers.manual_provider import ManualProvider, ManualResponsePending

MESSAGES = [{"role": "system", "content": "You are a test agent."}, {"role": "user", "content": "Do the task."}]


def test_first_call_writes_prompt_and_raises_pending(tmp_path):
    provider = ManualProvider()
    manual_dir = tmp_path / "manual_input"

    with pytest.raises(ManualResponsePending):
        provider.complete(MESSAGES, model="gemini-2.5-pro", temperature=0.7, max_tokens=1024, manual_dir=str(manual_dir), sample_idx=0)

    prompt_path = manual_dir / "prompt_00.md"
    assert prompt_path.exists()
    assert "Do the task." in prompt_path.read_text()
    assert not (manual_dir / "response_00.txt").exists()


def test_pasting_response_then_recalling_same_index_succeeds(tmp_path):
    """Re-running a survey (a fresh 'run this survey' click on a long-lived
    server, not just a fresh process) must re-request the same sample_idx
    and get the now-pasted answer, not advance past it."""
    provider = ManualProvider()
    manual_dir = tmp_path / "manual_input"

    with pytest.raises(ManualResponsePending):
        provider.complete(MESSAGES, model="gemini-2.5-pro", temperature=0.7, max_tokens=1024, manual_dir=str(manual_dir), sample_idx=0)

    (manual_dir / "response_00.txt").write_text('{"best": "PT", "worst": "C"}', encoding="utf-8")

    result = provider.complete(MESSAGES, model="gemini-2.5-pro", temperature=0.7, max_tokens=1024, manual_dir=str(manual_dir), sample_idx=0)
    assert result.text == '{"best": "PT", "worst": "C"}'
    assert result.finish_reason == "manual"


def test_different_sample_idx_uses_different_files(tmp_path):
    provider = ManualProvider()
    manual_dir = tmp_path / "manual_input"
    manual_dir.mkdir(parents=True)
    (manual_dir / "prompt_00.md").write_text("p0", encoding="utf-8")
    (manual_dir / "response_00.txt").write_text("r0", encoding="utf-8")

    first = provider.complete(MESSAGES, model="gemini-2.5-pro", temperature=0.7, max_tokens=1024, manual_dir=str(manual_dir), sample_idx=0)
    assert first.text == "r0"

    with pytest.raises(ManualResponsePending):
        provider.complete(MESSAGES, model="gemini-2.5-pro", temperature=0.7, max_tokens=1024, manual_dir=str(manual_dir), sample_idx=1)

    assert (manual_dir / "prompt_01.md").exists()
    assert not (manual_dir / "response_01.txt").exists()


def test_repair_attempt_uses_a_distinct_suffixed_file_pair(tmp_path):
    """attempt=0 keeps the original, suffix-free file names (backward
    compatible with in-progress human review workflows); a guardrails
    repair retry for the same sample_idx must write and read a separate
    prompt_NN_r1.md / response_NN_r1.txt pair, not silently no-op against
    the already-answered attempt-0 files."""
    provider = ManualProvider()
    manual_dir = tmp_path / "manual_input"

    with pytest.raises(ManualResponsePending):
        provider.complete(MESSAGES, model="gemini-2.5-pro", temperature=0.7, max_tokens=1024, manual_dir=str(manual_dir), sample_idx=0, attempt=0)
    (manual_dir / "response_00.txt").write_text("first (rejected) reply", encoding="utf-8")

    repair_messages = MESSAGES + [
        {"role": "assistant", "content": "first (rejected) reply"},
        {"role": "user", "content": "That response did not pass validation. Fix it."},
    ]
    with pytest.raises(ManualResponsePending):
        provider.complete(repair_messages, model="gemini-2.5-pro", temperature=0.7, max_tokens=1024, manual_dir=str(manual_dir), sample_idx=0, attempt=1)

    assert (manual_dir / "prompt_00.md").exists()
    assert (manual_dir / "prompt_00_r1.md").exists()
    assert "Fix it." in (manual_dir / "prompt_00_r1.md").read_text()
    assert not (manual_dir / "response_00_r1.txt").exists()

    (manual_dir / "response_00_r1.txt").write_text("corrected reply", encoding="utf-8")
    result = provider.complete(repair_messages, model="gemini-2.5-pro", temperature=0.7, max_tokens=1024, manual_dir=str(manual_dir), sample_idx=0, attempt=1)
    assert result.text == "corrected reply"
    # attempt 0's own response is untouched by the repair attempt.
    assert (manual_dir / "response_00.txt").read_text() == "first (rejected) reply"


def test_missing_manual_dir_kwarg_raises_provider_error():
    provider = ManualProvider()
    with pytest.raises(ProviderError):
        provider.complete(MESSAGES, model="gemini-2.5-pro", temperature=0.7, max_tokens=1024, sample_idx=0)


def test_missing_sample_idx_raises_provider_error(tmp_path):
    provider = ManualProvider()
    with pytest.raises(ProviderError):
        provider.complete(MESSAGES, model="gemini-2.5-pro", temperature=0.7, max_tokens=1024, manual_dir=str(tmp_path))
