import importlib.util
import pathlib
import sys
import unittest

SCRIPTS = pathlib.Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location("topic_crawl_fetch", SCRIPTS / "topic_crawl_fetch.py")
FETCH = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FETCH)


class KeywordPayloadTests(unittest.TestCase):
    def test_single_keyword_is_submitted_as_a_phrase(self):
        self.assertEqual({"keyword": "Singapore"}, FETCH.keyword_payload(["Singapore"]))

    def test_multiple_keywords_are_submitted_as_an_or_array(self):
        # A boolean-text join like "a OR b" is a literal phrase to the provider
        # and matches nothing; only the array form with keywordOper is a real OR.
        self.assertEqual(
            {"keyword": ["defence", "military"], "keywordOper": "or"},
            FETCH.keyword_payload(["defence", "military"]),
        )

    def test_empty_keywords_is_rejected(self):
        with self.assertRaises(ValueError):
            FETCH.keyword_payload([])


class ProviderWindowTests(unittest.TestCase):
    def test_singapore_day_maps_to_overlapping_utc_days(self):
        self.assertEqual(
            ("2026-09-27", "2026-09-28"),
            FETCH.provider_window("2026-09-28", "2026-09-28", "Asia/Singapore"),
        )

    def test_no_timezone_passes_dates_through(self):
        self.assertEqual(("2026-09-28", "2026-09-28"), FETCH.provider_window("2026-09-28", "2026-09-28", None))


if __name__ == "__main__":
    unittest.main()
