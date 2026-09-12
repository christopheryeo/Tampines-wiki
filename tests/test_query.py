import importlib.util
import json
import os
import pathlib
import unittest
from unittest import mock


SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "query.py"
SPEC = importlib.util.spec_from_file_location("query_under_test", SCRIPT)
QUERY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(QUERY)


def test_source_url_hyphens_preserve_query_metadata_and_summary(tmp_path, monkeypatch):
    entities = tmp_path / "entities"
    article = entities / "article" / "example.md"
    article.parent.mkdir(parents=True)
    article.write_text(
        "---\nsourceUrl: https://example.test/story---official\n"
        "publishedDate: '2026-05-31'\ntoneSentiment: Neutral\n---\n"
        "## Summary\nA report with --- in its body.\n## Key Points\n- A fact.\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(QUERY, "ROOT", tmp_path)
    monkeypatch.setattr(QUERY, "ENTITIES", entities)
    parsed = QUERY._parse_note("article", "example.md")
    assert parsed["frontmatter"]["sourceUrl"] == "https://example.test/story---official"
    assert parsed["frontmatter"]["publishedDate"] == "2026-05-31"
    assert parsed["frontmatter"]["toneSentiment"] == "Neutral"
    assert parsed["sections"]["summary"] == "A report with --- in its body."
    assert parsed["sections"]["key points"] == "- A fact."


def answered(answer="ok"):
    return {
        "answer": answer,
        "entities_resolved": ["chan-chun-sing"],
        "sources_cited": [],
        "status": "answered",
        "time_sensitive": False,
        "saf": True,
        "reused_query_id": None,
    }


class QueryFastPathTests(unittest.TestCase):
    def setUp(self):
        QUERY._CATALOG_CACHE.clear()

    def test_exact_name_alias_and_acronym_resolution(self):
        cases = {
            "Who is Chan Chun Sing?": ("people", "chan-chun-sing"),
            "Tell me more about Republic of Singapore Navy": ("organisations", "rsn"),
            "Who is the current CDF?": ("appointments", "cdf"),
        }
        for question, expected in cases.items():
            matches = QUERY._catalog_entity_matches(question)
            self.assertIn(expected, {(item["domain"], item["id"]) for item in matches})

    def test_query_shape_classification(self):
        cases = {
            "Who is Chan Chun Sing?": "identity",
            "Tell me more about RSN": "coverage",
            "How is Lawrence Wong related to Gan Kim Yong?": "relationship",
            "Give me a list of people who are related to defense": "roster",
            "Who is the current CDF?": "appointment",
            "So there is no cyber security breach in your wiki?": "existence",
        }
        for question, expected in cases.items():
            matches = QUERY._catalog_entity_matches(question)
            self.assertEqual(QUERY._query_shape(question, matches), expected)

    def test_fast_context_extracts_sections_and_stays_bounded(self):
        context = QUERY.build_fast_context("Who is Chan Chun Sing?")
        self.assertIsNotNone(context)
        self.assertEqual(context["query_shape"], "identity")
        self.assertEqual(
            [(item["domain"], item["id"]) for item in context["resolved_entities"]],
            [("people", "chan-chun-sing")],
        )
        encoded = json.dumps(context, ensure_ascii=False)
        self.assertIn("Singapore's Defence Minister", encoded)
        self.assertNotIn("## Coverage", encoded)
        self.assertLessEqual(len(encoded), QUERY.FAST_CONTEXT_CHAR_CAP)

    def test_roster_renders_related_people_locally(self):
        """The roster fast path renders a note's ## Related Entities / ### People.

        The note is supplied directly rather than read from the vault: the topic
        consolidation retired the broad hand-curated topic notes this test used
        to read, so pinning it to live vault data made it a taxonomy canary
        rather than a test of the rendering logic.
        """
        question = "Give me a list of people who are related to air capabilities"
        anchor = {
            "domain": "topic", "id": "air-capabilities",
            "displayName": "Air Capabilities", "file": "air-capabilities.md",
            "matched": "air-capabilities", "score": "0",
        }
        note = {
            "path": "entities/topic/air-capabilities.md",
            "frontmatter": {},
            "sections": {"related entities": (
                "### People\n"
                "- [[chan-chun-sing|Chan Chun Sing]]\n"
                "- [[kelvin-fan|Kelvin Fan]]\n\n"
                "### Organisations\n"
                "- [[rsaf|RSAF]]\n"
            )},
        }
        with mock.patch.object(QUERY, "_parse_note", return_value=note):
            result = QUERY._direct_roster_answer(question, [anchor])
        self.assertIsNotNone(result)
        self.assertTrue(result["answer"].startswith("2 people"))
        self.assertIn("1. Chan Chun Sing", result["answer"])
        self.assertIn("2. Kelvin Fan", result["answer"])
        self.assertNotIn("RSAF", result["answer"])
        self.assertEqual(result["entities_resolved"], ["air-capabilities"])
        self.assertEqual(result["sources_cited"], [])

    def test_appointment_renders_current_holder_locally(self):
        question = "Who is the current CDF?"
        result = QUERY._direct_appointment_answer(
            question, QUERY._catalog_entity_matches(question)
        )
        self.assertIn("VADM Aaron Beng", result["answer"])
        self.assertIn("As of 2026-03-31", result["answer"])
        self.assertEqual(result["entities_resolved"], ["cdf", "aaron-beng"])
        self.assertTrue(result["time_sensitive"])

    @mock.patch.object(QUERY, "_issue_catalog_matches", return_value=[])
    def test_negative_existence_context_expands_relevant_organisation_graph(self, issue_matches):
        context = QUERY.build_fast_context(
            "So there is no cyber security breach in your wiki?"
        )
        # No catalog entity matches this phrasing — the organisation graph is
        # discovered entirely by _existence_expansions. build_fast_context must
        # therefore not bail out on an empty match list for the existence shape.
        self.assertEqual(QUERY._catalog_entity_matches(
            "So there is no cyber security breach in your wiki?"
        ), [])
        self.assertIsNotNone(context)
        ids = {item["id"] for item in context["resolved_entities"]}
        self.assertEqual(
            ids,
            {"csa", "csit", "mindef", "sectoral-cyber-defence-team"},
        )
        self.assertEqual({item["id"] for item in context["entities"]}, ids)
        self.assertEqual(context["filed_issue_matches"], [])
        self.assertEqual(
            [target.split("-", 1)[0] for target in context["shared_coverage"]],
            ["993312", "993314", "993316", "993318", "993320", "994160"],
        )
        self.assertLessEqual(
            len(json.dumps(context, ensure_ascii=False)),
            QUERY.FAST_CONTEXT_CHAR_CAP,
        )

    def test_existence_context_preserves_a_filed_issue(self):
        filed = [{"id": "cyber-resilience", "displayName": "Cyber resilience", "matched_tokens": ["cyber"]}]
        with mock.patch.object(QUERY, "_issue_catalog_matches", return_value=filed):
            context = QUERY.build_fast_context("So there is no cyber security breach in your wiki?")
        self.assertEqual(context["filed_issue_matches"], filed)

    def test_undated_appointment_does_not_claim_verified_current_holder(self):
        note = {"frontmatter": {"currentHolder": "example-person"}, "sections": {
            "holders": "- [[example-person|Example Person]]", "office": "An office."}}
        with mock.patch.object(QUERY, "_parse_note", return_value=note):
            answer = QUERY._direct_appointment_answer("Who is the current holder?", [
                {"domain": "appointments", "file": "example.md", "id": "example", "displayName": "Example Office"}])
        self.assertIn("no verification date", answer["answer"])
        self.assertNotIn("is the current", answer["answer"])

    def test_golden_context_keeps_curated_source_anchors(self):
        cases = {
            "Who is Chan Chun Sing?": ["757551"],
            "Tell me more about RSN": [
                "793259", "801234", "1015627", "1008066", "1014225",
                "1029768", "1032776", "1004835", "1020721",
            ],
        }
        for question, expected in cases.items():
            context = QUERY.build_fast_context(question)
            sources = [
                item["target"].rstrip("/").split("/")[-1].split("-", 1)[0]
                for item in context["entities"][0]["coverage_evidence"]
            ]
            self.assertEqual(sources, expected)

        seletar = QUERY.build_fast_context(
            "What did people say about Seletar Aerospace Park?"
        )
        first = seletar["entities"][0]["coverage_evidence"][0]
        self.assertTrue(first["target"].startswith("782384-"))
        self.assertIn("Rolls-Royce", first["key_points"])

    def test_fast_model_uses_one_low_reasoning_request(self):
        payload = answered()
        payload["entities_resolved"].append("invented")
        payload["sources_cited"] = [
            "article/2025-11/782600-princess-anne", "invented-source",
        ]
        response = {
            "output": [{
                "type": "function_call",
                "name": "submit_answer",
                "arguments": json.dumps(payload),
            }]
        }
        with mock.patch.object(QUERY, "_call_responses", return_value=response) as call:
            result = QUERY._run_fast_model(
                "key", "gpt-5.6", "question", {
                    "resolved_entities": [{"id": "chan-chun-sing"}],
                    "shared_coverage": [],
                    "entities": [{
                        "coverage_evidence": [
                            {
                                "target": "782384-princess-anne",
                                "label": "PM Wong meets Princess Anne coverage",
                            },
                            {
                                "target": "article/2025-11/782600-princess-anne",
                                "label": "Prime Minister Wong Meets Visiting Princess Anne",
                            },
                        ],
                    }],
                },
            )
        self.assertEqual(result["answer"], "ok")
        self.assertEqual(result["entities_resolved"], ["chan-chun-sing"])
        self.assertEqual(result["sources_cited"], ["782384"])
        self.assertEqual(call.call_count, 1)
        self.assertEqual(call.call_args.kwargs["reasoning_effort"], "low")
        self.assertEqual(
            call.call_args.kwargs["tool_choice"],
            {"type": "function", "name": "submit_answer"},
        )

    def test_supported_query_routes_to_fast_model_without_fallback(self):
        with mock.patch.dict(os.environ, {
            "OPENAI_API_KEY": "test-key",
            "QUERY_FAST_PATH": "true",
        }, clear=False), \
             mock.patch.object(QUERY, "load_local_env"), \
             mock.patch.object(QUERY, "_run_fast_model",
                               return_value=answered()) as fast, \
             mock.patch.object(QUERY, "_run_legacy_model") as legacy:
            result = QUERY.run_query(
                "Who is Chan Chun Sing?", cache_read=False, cache_write=False
            )
        self.assertEqual(fast.call_count, 1)
        legacy.assert_not_called()
        self.assertFalse(result["cache_written"])

    def test_ambiguous_resolution_routes_to_legacy_fallback(self):
        ambiguous = [
            {"domain": "people", "id": "one", "displayName": "One",
             "file": "one.md", "matched": "One", "score": "100"},
            {"domain": "people", "id": "two", "displayName": "Two",
             "file": "two.md", "matched": "Two", "score": "100"},
        ]
        with mock.patch.dict(os.environ, {
            "OPENAI_API_KEY": "test-key",
            "QUERY_FAST_PATH": "true",
        }, clear=False), \
             mock.patch.object(QUERY, "load_local_env"), \
             mock.patch.object(QUERY, "_catalog_entity_matches",
                               return_value=ambiguous), \
             mock.patch.object(QUERY, "_run_fast_model") as fast, \
             mock.patch.object(QUERY, "_run_legacy_model",
                               return_value=answered("legacy")) as legacy:
            result = QUERY.run_query(
                "Who is One?", cache_read=False, cache_write=False
            )
        fast.assert_not_called()
        self.assertEqual(legacy.call_count, 1)
        self.assertEqual(result["answer"], "legacy")

    def test_cache_read_and_rollback_switch_preserve_legacy_path(self):
        for environment, cache_read in (
            ({"QUERY_FAST_PATH": "true"}, True),
            ({"QUERY_FAST_PATH": "false"}, False),
        ):
            with self.subTest(environment=environment, cache_read=cache_read), \
                 mock.patch.dict(os.environ, {
                     "OPENAI_API_KEY": "test-key", **environment,
                 }, clear=False), \
                 mock.patch.object(QUERY, "load_local_env"), \
                 mock.patch.object(QUERY, "_run_fast_model") as fast, \
                 mock.patch.object(QUERY, "_run_legacy_model",
                                   return_value=answered("legacy")) as legacy:
                result = QUERY.run_query(
                    "Who is Chan Chun Sing?",
                    cache_read=cache_read,
                    cache_write=False,
                )
            fast.assert_not_called()
            self.assertEqual(legacy.call_count, 1)
            self.assertEqual(result["answer"], "legacy")

    def test_fast_answer_keeps_cache_write_behavior(self):
        with mock.patch.dict(os.environ, {
            "OPENAI_API_KEY": "test-key",
            "QUERY_FAST_PATH": "true",
        }, clear=False), \
             mock.patch.object(QUERY, "load_local_env"), \
             mock.patch.object(QUERY, "_run_fast_model",
                               return_value=answered()), \
             mock.patch.object(QUERY, "persist_answer",
                               return_value={"query_id": "saved"}) as persist:
            result = QUERY.run_query(
                "Who is Chan Chun Sing?", cache_read=False, cache_write=True
            )
        persist.assert_called_once()
        self.assertTrue(result["cache_written"])
        self.assertEqual(result["query_id"], "saved")


if __name__ == "__main__":
    unittest.main()
