import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from symphysis.reporting import render_methodology_section, render_per_agent_detail_section


def test_methodology_section_names_the_instrument_and_agent_count():
    text = render_methodology_section("bwm", 3, [])
    assert "Best-Worst Method" in text
    assert "3 agent response" in text
    assert "SHA-256 integrity manifest" in text


def test_methodology_section_embeds_chart_images_with_relative_paths():
    text = render_methodology_section("ahp", 1, [Path("/some/absolute/path/report/charts/ahp_aggregated_weights.png")])
    assert "![Ahp Aggregated Weights](charts/ahp_aggregated_weights.png)" in text


def test_methodology_section_handles_an_unknown_instrument_without_raising():
    text = render_methodology_section("delphi", 2, [])
    assert "delphi" in text


def test_per_agent_detail_section_includes_reasoning_and_sources():
    detail = [
        {
            "agent_id": "a1",
            "display_name": "Data Engineer A",
            "role": "Data Engineer",
            "model": "ollama/mistral:7b",
            "did": "did:key:abc123",
            "qa_precheck_passed": True,
            "answer": {"best": "Q", "worst": "C"},
            "reasoning": "Quality matters most because of downstream pipeline reliability.",
            "sources_used": ["role knowledge: data_engineer"],
        }
    ]
    text = render_per_agent_detail_section(detail)
    assert "Data Engineer A" in text
    assert "did:key:abc123" in text
    assert "QA precheck: passed" in text
    assert "role knowledge: data_engineer" in text
    assert "Quality matters most" in text
    assert '"best": "Q"' in text


def test_per_agent_detail_section_flags_a_failed_qa_precheck():
    detail = [
        {
            "agent_id": "a1", "display_name": None, "role": "R", "model": "m", "did": "did:key:x",
            "qa_precheck_passed": False, "answer": {}, "reasoning": "r", "sources_used": None,
        }
    ]
    text = render_per_agent_detail_section(detail)
    assert "QA precheck: FAILED" in text
    assert "Sources used: (not reported)" in text


def test_per_agent_detail_section_handles_no_agents():
    text = render_per_agent_detail_section([])
    assert "No agent contributed" in text
