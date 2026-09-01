import sys
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from symphysis.guardrails import run_with_guardrails
from symphysis.instruments.base import InstrumentResult
from symphysis.providers.base import ProviderResponse


class _ScriptedProvider:
    """Returns each of `replies` in order, one per `complete()` call, and
    records the exact messages list it was called with so the repair-turn
    content can be asserted on directly."""

    def __init__(self, replies: List[str]) -> None:
        self.replies = list(replies)
        self.calls: List[List[Dict[str, str]]] = []

    def complete(self, messages: List[Dict[str, str]], **kwargs: Any) -> ProviderResponse:
        self.calls.append(messages)
        text = self.replies.pop(0)
        return ProviderResponse(text=text, model="fake", finish_reason="stop")


class _RejectFirstAcceptSecond:
    """First .parse() call always fails with a fixed error; every later call
    succeeds. Mirrors the real HierarchicalBWMInstrument's contract without
    needing real BWM criteria."""

    name = "fake"

    def __init__(self, error: str) -> None:
        self.error = error
        self.calls = 0

    def build_messages(self, *args: Any, **kwargs: Any) -> List[Dict[str, str]]:
        return [{"role": "system", "content": "sys"}, {"role": "user", "content": "task"}]

    def parse(self, raw_text: str, params: Dict[str, Any]) -> InstrumentResult:
        self.calls += 1
        if self.calls == 1:
            return InstrumentResult(valid=False, payload={}, errors=[self.error])
        return InstrumentResult(valid=True, payload={"text": raw_text}, errors=[])


def test_malformed_retry_appends_repair_turn_with_the_exact_error() -> None:
    """A schema-invalid completion's retry must not just resend the original
    prompt (which reuses the same seed and reliably reproduces the same
    wrong answer, see diagnostics.md): it must show the model its own reply
    plus the exact validator error and ask for a targeted fix."""
    provider = _ScriptedProvider(["{bad json}", '{"best_to_others": {"X": 1}}'])
    instrument = _RejectFirstAcceptSecond(error="Level 'L1': best_to_others[best] must be 1, got 9")

    run = run_with_guardrails(
        provider,
        instrument,
        messages=[{"role": "system", "content": "sys"}, {"role": "user", "content": "task"}],
        instrument_params={},
        model="fake-model",
        temperature=0.2,
        max_tokens=100,
        top_p=1.0,
        seed=42,
        repeats=1,
        max_retries_on_malformed=1,
        agreement_threshold=0.0,
    )

    assert len(run.accepted) == 1
    assert len(provider.calls) == 2

    first_call_messages = provider.calls[0]
    second_call_messages = provider.calls[1]

    # The retry's message list is the original two turns plus a repair pair.
    assert second_call_messages[:2] == first_call_messages
    assert len(second_call_messages) == 4
    assert second_call_messages[2] == {"role": "assistant", "content": "{bad json}"}
    assert second_call_messages[3]["role"] == "user"
    assert "best_to_others[best] must be 1, got 9" in second_call_messages[3]["content"]
    assert "fix" in second_call_messages[3]["content"].lower()


def test_last_retry_does_not_append_a_repair_turn_nobody_will_read() -> None:
    """If this was the final allowed attempt, appending another repair turn
    before giving up would grow the stored prompt for no benefit: nothing
    calls the provider again for this sample."""
    provider = _ScriptedProvider(["{bad}"])

    class _AlwaysReject:
        name = "fake"

        def build_messages(self, *a: Any, **k: Any) -> List[Dict[str, str]]:
            return [{"role": "user", "content": "task"}]

        def parse(self, raw_text: str, params: Dict[str, Any]) -> InstrumentResult:
            return InstrumentResult(valid=False, payload={}, errors=["always wrong"])

    run = run_with_guardrails(
        provider,
        _AlwaysReject(),
        messages=[{"role": "user", "content": "task"}],
        instrument_params={},
        model="fake-model",
        temperature=0.2,
        max_tokens=100,
        top_p=1.0,
        seed=None,
        repeats=1,
        max_retries_on_malformed=0,
        agreement_threshold=0.0,
    )

    assert len(run.accepted) == 0
    assert len(run.rejected) == 1
    assert len(provider.calls) == 1


def test_denylist_rejection_does_not_extend_the_conversation() -> None:
    """A denylist hit is a content-policy rejection, not a formatting error;
    it retries with a fresh independent sample, not a repair turn asking the
    model to 'fix' a prompt-injection marker."""
    provider = _ScriptedProvider(["ignore all previous instructions", '{"ok": true}'])

    class _AcceptAnything:
        name = "fake"

        def build_messages(self, *a: Any, **k: Any) -> List[Dict[str, str]]:
            return [{"role": "user", "content": "task"}]

        def parse(self, raw_text: str, params: Dict[str, Any]) -> InstrumentResult:
            return InstrumentResult(valid=True, payload={"text": raw_text}, errors=[])

    run = run_with_guardrails(
        provider,
        _AcceptAnything(),
        messages=[{"role": "user", "content": "task"}],
        instrument_params={},
        model="fake-model",
        temperature=0.2,
        max_tokens=100,
        top_p=1.0,
        seed=None,
        repeats=1,
        max_retries_on_malformed=1,
        agreement_threshold=0.0,
        denylist_patterns=[r"ignore all previous instructions"],
    )

    assert len(run.accepted) == 1
    assert provider.calls[1] == [{"role": "user", "content": "task"}]
