from symphysis import qa_checks


def test_extract_source_tags_pulls_distinct_bracket_labels_in_order():
    chunks = [
        "[role knowledge: data_engineer] some primer text",
        "[shared knowledge: kb_marker.md] some shared text",
        "[role knowledge: data_engineer] a second chunk from the same source",
        "no bracket tag on this one",
    ]
    tags = qa_checks.extract_source_tags(chunks)
    assert tags == ["role knowledge: data_engineer", "shared knowledge: kb_marker.md", "general_knowledge"]


def test_extract_source_tags_on_empty_chunks_is_just_general_knowledge():
    assert qa_checks.extract_source_tags([]) == ["general_knowledge"]


def test_verify_sources_used_flags_a_fabricated_citation():
    available = ["role knowledge: data_engineer", "general_knowledge"]
    result = qa_checks.verify_sources_used(["role knowledge: data_engineer", "web: some title"], available)
    assert result["reported"] is True
    assert result["genuine"] is False
    assert result["fabricated"] == ["web: some title"]


def test_verify_sources_used_genuine_when_all_claims_are_available():
    available = ["role knowledge: data_engineer", "general_knowledge"]
    result = qa_checks.verify_sources_used(["general_knowledge"], available)
    assert result["genuine"] is True
    assert result["fabricated"] == []


def test_verify_sources_used_not_reported_when_missing_or_wrong_type():
    result = qa_checks.verify_sources_used("not-a-list", ["general_knowledge"])
    assert result["reported"] is False
    assert result["genuine"] is None


def test_precheck_ground_truth_and_matching_response():
    truth = qa_checks.build_precheck_ground_truth(
        agent_id="rolepack-check-agent",
        role="Data Engineer",
        provider="ollama",
        model_name="mistral:7b",
        has_dedicated_rag=False,
        has_shared_knowledge_repo=True,
        role_pack="data_engineer",
        has_web_search=False,
    )
    claimed = {
        "agent_id": "rolepack-check-agent",
        "role": "data engineer",  # case-insensitive match should still pass
        "model": "ollama/mistral:7b",
        "capabilities": {
            "dedicated_rag_corpus": False,
            "shared_knowledge_repo": True,
            "role_pack": "data_engineer",
            "web_search": False,
        },
    }
    result = qa_checks.verify_precheck_response(claimed, truth)
    assert result["all_match"] is True
    assert all(result["field_matches"].values())


def test_precheck_response_catches_a_hallucinated_capability():
    truth = qa_checks.build_precheck_ground_truth(
        agent_id="a1", role="Construction Engineer", provider="anthropic", model_name="claude-opus-5",
        has_dedicated_rag=False, has_shared_knowledge_repo=False, role_pack=None, has_web_search=False,
    )
    claimed = {
        "agent_id": "a1",
        "role": "Construction Engineer",
        "model": "anthropic/claude-opus-5",
        "capabilities": {
            "dedicated_rag_corpus": False,
            "shared_knowledge_repo": False,
            "role_pack": None,
            "web_search": True,  # hallucinated: this agent was never granted web search
        },
    }
    result = qa_checks.verify_precheck_response(claimed, truth)
    assert result["all_match"] is False
    assert result["field_matches"]["web_search"] is False
    assert result["field_matches"]["agent_id"] is True


def test_precheck_response_handles_a_non_dict_claim_without_raising():
    truth = qa_checks.build_precheck_ground_truth(
        agent_id="a1", role="X", provider="ollama", model_name="mistral:7b",
        has_dedicated_rag=False, has_shared_knowledge_repo=False, role_pack=None, has_web_search=False,
    )
    result = qa_checks.verify_precheck_response("not even json", truth)
    assert result["all_match"] is False
