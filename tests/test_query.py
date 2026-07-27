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

    def test_roster_renders_live_related_people_locally(self):
        question = "Give me a list of people who are related to defense"
        matches = QUERY._catalog_entity_matches(question)
        result = QUERY._direct_roster_answer(question, matches)
        self.assertIsNotNone(result)
        defence = QUERY._parse_note("topic", "defence")
        expected_count = len(QUERY._WIKILINK_RE.findall(
            QUERY._subsection(QUERY._section(defence, "Related Entities"), "People")
        ))
        self.assertTrue(result["answer"].startswith(f"{expected_count} people"))
        self.assertEqual(result["entities_resolved"], ["defence"])
        self.assertEqual(result["sources_cited"], [])

    def test_appointment_renders_current_holder_locally(self):
        question = "Who is the current CDF?"
        result = QUERY._direct_appointment_answer(
            question, QUERY._catalog_entity_matches(question)
        )
        self.assertIn("VADM Aaron Beng", result["answer"])
        self.assertEqual(result["entities_resolved"], ["cdf", "aaron-beng"])
        self.assertTrue(result["time_sensitive"])

    def test_negative_existence_context_expands_relevant_organisation_graph(self):
        context = QUERY.build_fast_context(
            "So there is no cyber security breach in your wiki?"
        )
        ids = {item["id"] for item in context["resolved_entities"]}
        self.assertEqual(
            ids,
            {"csa", "csit", "mindef", "sectoral-cyber-defence-team"},
        )
        self.assertIn(
            "cyber-security",
            {item["id"] for item in context["entities"]},
        )
        self.assertEqual(context["filed_issue_matches"], [])
        self.assertEqual(
            [target.split("-", 1)[0] for target in context["shared_coverage"]],
            ["993312", "993314", "993316", "993318", "993320", "994160"],
        )
        self.assertLessEqual(
            len(json.dumps(context, ensure_ascii=False)),
            QUERY.FAST_CONTEXT_CHAR_CAP,
        )

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
