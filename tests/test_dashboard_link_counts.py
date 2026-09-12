"""Regression coverage for dashboard undercounts of canonical wiki links."""

import importlib.util
from pathlib import Path


spec = importlib.util.spec_from_file_location(
    "dashboard_generator",
    Path(__file__).resolve().parents[1]
    / "dashboards/site/scripts/generate_dashboard_data.py",
)
dashboard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dashboard)


def test_resolves_domain_paths_and_ignores_evidence_copies():
    body = """## Summary
[[people/alex|Alex]] met [[organisations/agency|Agency]].
[[entities/people/alex.md#Coverage|Alex]] and [[alex|Alex]] returned.
## Source Text
The source literally contains [[people/alex|Alex]].
## Database Projection
{"description": "[[people/alex|Alex]]"}
"""
    assert dashboard.article_link_domains(
        body,
        {"people/alex": "people", "organisations/agency": "organisations"},
        {"alex": {"people"}, "agency": {"organisations"}},
    ) == {"people": 3, "organisations": 1}


def test_ambiguous_basenames_and_missing_targets_are_not_counted():
    body = "[[victoria|Victoria]] [[place/victoria|Place]] [[missing|Missing]]"
    assert dashboard.article_link_domains(
        body,
        {"people/victoria": "people", "place/victoria": "place"},
        {"victoria": {"people", "place"}},
    ) == {"place": 1}


def test_projection_without_source_heading_is_also_excluded():
    body = "## Summary\n[[alex|Alex]]\n## Database Projection\n[[alex|Alex]]"
    assert dashboard.article_link_domains(body, {}, {"alex": {"people"}}) == {
        "people": 1
    }
