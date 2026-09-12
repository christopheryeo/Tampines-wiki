import importlib.util
from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "topic_consolidation", ROOT / "scripts" / "topic_consolidation.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


def test_unquoted_flow_definition_is_rejected_instead_of_silently_truncated(tmp_path):
    rows = [
        f'  - {{topicId: topic-{i}, displayName: Topic {i}, category: Security, '
        'keywords: [security], definition: Security, defence and cooperation.}'
        for i in range(60)
    ]
    path = tmp_path / "taxonomy.yaml"
    path.write_text("maximumActiveTopics: 100\ntopics:\n" + "\n".join(rows))
    with pytest.raises(MODULE.ConsolidationError, match="unexpected fields.*quoting"):
        MODULE.load_taxonomy(path)


def test_quoted_definition_preserves_commas_and_other_topic_fields(tmp_path):
    payload = yaml.safe_load(MODULE.TAXONOMY_PATH.read_text())
    payload["topics"][0]["definition"] = "Security, defence and cooperation."
    path = tmp_path / "taxonomy.yaml"
    path.write_text(yaml.safe_dump(payload, default_flow_style=True, sort_keys=False))
    _, topics = MODULE.load_taxonomy(path)
    assert topics[0]["definition"] == "Security, defence and cooperation."
    for expected, actual in zip(payload["topics"], topics):
        assert {key: actual[key] for key in expected} == expected


def test_taxonomy_is_inside_approved_range_and_unique():
    payload, topics = MODULE.load_taxonomy()
    ids = [row["topicId"] for row in topics]
    assert 60 <= len(topics) <= payload["maximumActiveTopics"] <= MODULE.ABSOLUTE_MAXIMUM_ACTIVE_TOPICS
    assert len(ids) == len(set(ids))
    assert payload["assignmentLimit"] == 3


def test_weak_nonzero_score_still_selects_primary():
    _, topics = MODULE.load_taxonomy()
    fragments = {
        "sourceId": "x",
        "title": "Aviation",
        "projectionTopic": "",
        "issueTags": [],
        "topicLinks": [],
        "summary": "",
        "keyPoints": "",
        "category": "",
    }
    result = MODULE.classify(fragments, topics)
    assert result["primary"] == "air-capabilities"
    assert not result["fallback"]


def test_unmatched_article_uses_auditable_general_fallback():
    _, topics = MODULE.load_taxonomy()
    fragments = {
        "sourceId": "x",
        "title": "Completely unrelated placeholder",
        "projectionTopic": "",
        "issueTags": [],
        "topicLinks": [],
        "summary": "",
        "keyPoints": "",
        "category": "",
    }
    result = MODULE.classify(fragments, topics)
    assert result["primary"] == "general-defence-security"
    assert result["fallback"]
