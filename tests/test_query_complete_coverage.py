import importlib.util
import json
from pathlib import Path

import pytest


spec = importlib.util.spec_from_file_location("complete_coverage_query", Path(__file__).resolve().parents[1] / "scripts/query.py")
query = importlib.util.module_from_spec(spec)
spec.loader.exec_module(query)


@pytest.fixture
def corpus(tmp_path, monkeypatch):
    entities = tmp_path / "entities"
    (entities / "country").mkdir(parents=True)
    articles = entities / "article/2026-01"
    articles.mkdir(parents=True)
    for index in range(25):
        (articles / f"item-{index:02}.md").write_text(
            f"---\nsourceId: '{index}'\npublishedDate: '2026-01-{index + 1:02}'\ntags: ['#saf']\n---\n"
            f"# Report {index}\n\n## Summary\nRetained summary {index}.\n"
        )
    anchors = []
    for name in ["alpha", "beta"]:
        links = [f"- [[{'article/2026-01/' if name == 'alpha' else ''}item-{i:02}|Report {i}]]" for i in range(24, -1, -1)]
        # Same article in two link forms must not inflate membership.
        links.append("- [[article/2026-01/item-00|Repeated reference]]")
        (entities / "country" / f"{name}.md").write_text(
            f"---\ndisplayName: {name.title()}\n---\n## Coverage\n" + "\n".join(links) + "\n"
        )
        anchors.append({"domain": "country", "id": name, "file": name + ".md", "displayName": name.title()})
    monkeypatch.setattr(query, "ROOT", tmp_path)
    monkeypatch.setattr(query, "ENTITIES", entities)
    return entities, anchors


def test_complete_shared_list_normalizes_links_and_exceeds_twenty(corpus):
    _, anchors = corpus
    answer = query._direct_coverage_answer("Which articles are shared by Alpha and Beta?", anchors)
    assert answer["status"] == "answered"
    assert len(answer["sources_cited"]) == 25
    assert answer["sources_cited"][0] == "article/2026-01/item-00"
    assert answer["sources_cited"][-1] == "article/2026-01/item-24"
    assert "25 shared coverage articles" in answer["answer"]
    assert "2026-01-01 — Report 0" in answer["answer"]
    assert answer["saf"] is True


def test_complete_chronology_and_descending_order(corpus):
    _, anchors = corpus
    oldest = query._direct_coverage_answer("List every Coverage article for Alpha, oldest first.", anchors[:1])
    newest = query._direct_coverage_answer("List every Coverage article for Alpha, newest first.", anchors[:1])
    assert oldest["sources_cited"] == list(reversed(newest["sources_cited"]))
    assert oldest["answer"].index("2026-01-01") < oldest["answer"].index("2026-01-25")


def test_missing_reference_prevents_complete_claim(corpus):
    entities, anchors = corpus
    with (entities / "country/alpha.md").open("a") as file:
        file.write("- [[missing-article|Missing]]\n")
    answer = query._direct_coverage_answer("List all articles for Alpha.", anchors[:1])
    assert answer["status"] == "unresolved"
    assert answer["sources_cited"] == []


def test_date_filter_is_not_silently_ignored(corpus):
    _, anchors = corpus
    assert query._direct_coverage_answer("List all articles for Alpha since 2026.", anchors[:1]) is None


def test_run_query_complete_list_needs_no_external_call(corpus, monkeypatch):
    _, anchors = corpus
    monkeypatch.setattr(query, "load_local_env", lambda: None)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(query, "_catalog_entity_matches", lambda _: anchors)
    monkeypatch.setattr(query, "fast_path_enabled", lambda: True)
    monkeypatch.setattr(query, "_call_responses", lambda *a, **k: pytest.fail("Unexpected external call"))
    answer = query.run_query("Which articles are shared by Alpha and Beta?", cache_read=False, cache_write=False)
    assert len(answer["sources_cited"]) == 25
    assert answer["cache_written"] is False


def test_legacy_title_and_undated_entry_are_preserved(corpus):
    entities, anchors = corpus
    path = entities / "article/2026-01/item-00.md"
    path.write_text("---\nsourceId: '0'\n---\n## Summary\nLegacy.\n## Database Projection\n```json\n" + json.dumps({"article": {"article_title": "Legacy report title"}}) + "\n```\n")
    answer = query._direct_coverage_answer("List all articles for Alpha.", anchors[:1])
    assert answer["sources_cited"][-1] == "article/2026-01/item-00"
    assert "Date unavailable — Legacy report title" in answer["answer"]
