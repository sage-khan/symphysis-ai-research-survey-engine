from agentic_survey import role_packs


def test_list_role_packs_finds_the_shipped_packs_with_unique_ids():
    packs = role_packs.list_role_packs()
    ids = [p["id"] for p in packs]
    assert len(ids) == len(set(ids))
    assert "data_engineer" in ids
    assert "ai_scientist" in ids
    for p in packs:
        assert p["label"]
        assert p["summary"]


def test_get_role_pack_text_returns_the_body_without_the_header():
    text = role_packs.get_role_pack_text("data_engineer")
    assert text
    assert not text.startswith("#")
    assert not text.startswith("Summary:")
    assert "ISO/IEC 25012" in text


def test_get_role_pack_text_returns_none_for_unset_or_unknown_pack():
    assert role_packs.get_role_pack_text(None) is None
    assert role_packs.get_role_pack_text("") is None
    assert role_packs.get_role_pack_text("nonexistent-pack-id") is None


def test_every_shipped_pack_has_nonempty_body():
    for p in role_packs.list_role_packs():
        text = role_packs.get_role_pack_text(p["id"])
        assert text and len(text) > 200
