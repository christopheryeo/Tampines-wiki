import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("generate_catalog", ROOT / "scripts" / "generate_catalog.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_find_notes_excludes_monthly_append_only_logs(tmp_path):
    (tmp_path / "entity.md").write_text("---\nid: entity\n---\n", encoding="utf-8")
    (tmp_path / "log.md").write_text("ledger\n", encoding="utf-8")
    (tmp_path / "log-2026-08.md").write_text("monthly ledger\n", encoding="utf-8")
    assert [Path(path).name for path in MODULE.find_notes(str(tmp_path))] == ["entity.md"]


def test_find_notes_excludes_dropbox_conflicted_copies(tmp_path):
    (tmp_path / "entity.md").write_text("---\nid: entity\n---\n", encoding="utf-8")
    (tmp_path / "entity (Chris Yeo's conflicted copy 2026-08-18).md").write_text(
        "---\nid: entity\n---\n", encoding="utf-8"
    )
    assert [Path(path).name for path in MODULE.find_notes(str(tmp_path))] == ["entity.md"]


def test_source_url_hyphens_do_not_truncate_article_metadata(tmp_path):
    note = tmp_path / "article.md"
    note.write_text(
        "---\nsourceUrl: https://example.test/story---official\n"
        "publishedDate: '2026-05-31'\ntoneSentiment: Neutral\n---\n## Summary\nReport.\n",
        encoding="utf-8",
    )
    metadata = MODULE.parse_frontmatter(note)
    assert metadata["sourceUrl"] == "https://example.test/story---official"
    assert metadata["publishedDate"] == "2026-05-31"
    assert metadata["toneSentiment"] == "Neutral"
