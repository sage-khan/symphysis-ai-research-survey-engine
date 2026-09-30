import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from symphysis.audit.logger import SurveyStorage
from symphysis.spawning import lineage


def test_append_and_read_back_root_spawn(tmp_path):
    storage = SurveyStorage(tmp_path / "survey")
    lineage.append(storage, child_did="did:key:zRoot", child_agent_id="root-agent", parent_did=None)

    edges = lineage._read(storage)
    assert len(edges) == 1
    assert edges[0]["child_did"] == "did:key:zRoot"
    assert edges[0]["parent_did"] is None
    assert "declared_at" in edges[0]


def test_append_accumulates_multiple_edges(tmp_path):
    storage = SurveyStorage(tmp_path / "survey")
    lineage.append(storage, child_did="did:key:zParent", child_agent_id="parent", parent_did=None)
    lineage.append(storage, child_did="did:key:zChild", child_agent_id="child", parent_did="did:key:zParent")

    edges = lineage._read(storage)
    assert len(edges) == 2


def test_tree_groups_by_parent_did_using_root_sentinel_for_none(tmp_path):
    storage = SurveyStorage(tmp_path / "survey")
    lineage.append(storage, child_did="did:key:zA", child_agent_id="a", parent_did=None)
    lineage.append(storage, child_did="did:key:zB", child_agent_id="b", parent_did=None)
    lineage.append(storage, child_did="did:key:zC", child_agent_id="c", parent_did="did:key:zA")

    grouped = lineage.tree(storage)
    assert len(grouped["root"]) == 2
    assert len(grouped["did:key:zA"]) == 1
    assert grouped["did:key:zA"][0]["child_agent_id"] == "c"


def test_tree_on_empty_survey_is_empty_dict(tmp_path):
    storage = SurveyStorage(tmp_path / "survey")
    assert lineage.tree(storage) == {}
