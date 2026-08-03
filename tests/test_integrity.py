from pathlib import Path

from agentic_survey import integrity


def _make_survey_dir(tmp_path: Path) -> Path:
    d = tmp_path / "survey"
    (d / "agents" / "a1").mkdir(parents=True)
    (d / "report").mkdir()
    (d / "survey.yaml").write_text("id: test\n", encoding="utf-8")
    (d / "agents" / "a1" / "result.json").write_text('{"best": "c1"}', encoding="utf-8")
    (d / "report" / "report.md").write_text("# Report\n", encoding="utf-8")
    return d


def test_write_manifest_creates_json_and_sha256sums(tmp_path):
    d = _make_survey_dir(tmp_path)
    manifest = integrity.write_manifest(d)

    assert (d / integrity.MANIFEST_FILENAME).exists()
    assert (d / integrity.SHA256SUMS_FILENAME).exists()
    assert manifest["file_count"] == 3
    assert "survey.yaml" in manifest["files"]
    assert len(manifest["root_hash"]) == 64  # hex sha256


def test_manifest_excludes_its_own_files(tmp_path):
    d = _make_survey_dir(tmp_path)
    integrity.write_manifest(d)
    hashes = integrity.compute_file_hashes(d)
    assert integrity.MANIFEST_FILENAME not in hashes
    assert integrity.SHA256SUMS_FILENAME not in hashes


def test_root_hash_is_stable_regardless_of_dict_order(tmp_path):
    a = {"x": "1111", "y": "2222"}
    b = {"y": "2222", "x": "1111"}
    assert integrity.compute_root_hash(a) == integrity.compute_root_hash(b)


def test_verify_passes_when_nothing_changed(tmp_path):
    d = _make_survey_dir(tmp_path)
    integrity.write_manifest(d)
    result = integrity.verify(d)
    assert result.ok is True
    assert result.changed == []
    assert result.added == []
    assert result.removed == []


def test_verify_detects_a_changed_file(tmp_path):
    d = _make_survey_dir(tmp_path)
    integrity.write_manifest(d)
    (d / "report" / "report.md").write_text("# Altered report\n", encoding="utf-8")
    result = integrity.verify(d)
    assert result.ok is False
    assert "report/report.md" in result.changed


def test_verify_detects_an_added_file(tmp_path):
    d = _make_survey_dir(tmp_path)
    integrity.write_manifest(d)
    (d / "agents" / "a1" / "new_file.json").write_text("{}", encoding="utf-8")
    result = integrity.verify(d)
    assert result.ok is False
    assert "agents/a1/new_file.json" in result.added


def test_verify_detects_a_removed_file(tmp_path):
    d = _make_survey_dir(tmp_path)
    integrity.write_manifest(d)
    (d / "report" / "report.md").unlink()
    result = integrity.verify(d)
    assert result.ok is False
    assert "report/report.md" in result.removed


def test_verify_without_a_manifest_reports_not_ok(tmp_path):
    d = _make_survey_dir(tmp_path)
    result = integrity.verify(d)
    assert result.ok is False
    assert result.manifest_root_hash is None


def test_sha256sums_file_is_sha256sum_dash_c_compatible_format(tmp_path):
    d = _make_survey_dir(tmp_path)
    integrity.write_manifest(d)
    content = (d / integrity.SHA256SUMS_FILENAME).read_text(encoding="utf-8")
    for line in content.strip().splitlines():
        hash_part, path_part = line.split("  ", 1)
        assert len(hash_part) == 64
        assert all(c in "0123456789abcdef" for c in hash_part)
