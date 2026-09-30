"""Tests for policy/engine.py's Phase 4 escalation predicates
(docs/architecture/governance-layer-and-runtime-backends-plan.md §4):
escalated_level_ids/should_escalate are pure, instrument-agnostic functions
over already-loaded level definitions (the shape
HierarchicalBWMInstrument.levels_for_panel() returns), with no import-time
dependency on any one instrument module."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from symphysis.policy.engine import escalated_level_ids, should_escalate

LEVELS = [
    {"id": "L1", "dimensions": ["A", "B"]},
    {"id": "L2", "dimensions": ["A", "B", "C", "D", "E", "F", "G"]},
    {"id": "L3", "dimensions": ["A", "B", "C"]},
]


def test_escalated_level_ids_returns_only_levels_over_threshold():
    assert escalated_level_ids(LEVELS, threshold=6) == ["L2"]


def test_escalated_level_ids_returns_empty_when_nothing_exceeds_threshold():
    assert escalated_level_ids(LEVELS, threshold=10) == []


def test_escalated_level_ids_threshold_is_strictly_greater_than_not_equal():
    # A level with exactly `threshold` dimensions does not escalate; only
    # "more than N criteria" (per the plan doc's own wording) does.
    assert escalated_level_ids(LEVELS, threshold=3) == ["L2"]
    assert "L3" not in escalated_level_ids(LEVELS, threshold=3)


def test_escalated_level_ids_can_return_multiple_levels():
    assert escalated_level_ids(LEVELS, threshold=2) == ["L2", "L3"]


def test_escalated_level_ids_handles_a_level_missing_dimensions_key():
    assert escalated_level_ids([{"id": "L0"}], threshold=0) == []


def test_should_escalate_true_when_any_level_exceeds_threshold():
    assert should_escalate(LEVELS, threshold=6) is True


def test_should_escalate_false_when_no_level_exceeds_threshold():
    assert should_escalate(LEVELS, threshold=10) is False


def test_should_escalate_false_on_empty_levels():
    assert should_escalate([], threshold=0) is False
