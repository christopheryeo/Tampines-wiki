import importlib.util
import pathlib
import tempfile
import unittest


SCRIPT_DIR = pathlib.Path(__file__).resolve().parents[1] / "scripts"
SPEC = importlib.util.spec_from_file_location(
    "build_topic_crawl_log",
    SCRIPT_DIR / "build_topic_crawl_log.py",
)
BUILDER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILDER)


class BuildTopicCrawlLogTests(unittest.TestCase):
    def test_bulk_run_exception_transition_lines_are_recognized_as_an_episode(self):
        """scripts/end_topic_crawl.md's bulk-run exception (and
        update_topic_crawl_status.md) write audit lines as
        'action: crawlStatus <From> -> <To>'. ACTION_RE's action group only
        matches lowercase letters/spaces right after 'crawl', so it never
        matched 'crawlStatus' (capital S) at all -- these lines were silently
        dropped entirely, and every topic's per-topic Crawl Log section
        stopped showing any bulk-run-exception-era episode.
        """
        with tempfile.TemporaryDirectory() as temporary:
            topic_root = pathlib.Path(temporary)
            (topic_root / "general-defence-security.md").write_text(
                "---\ntopicId: general-defence-security\ndisplayName: General Defence and Security\n"
                "crawlStatus: Completed\ncrawlStatusAt: 2026-10-10T03:16:22+08:00\n"
                "lastCrawledAt: 2026-10-10T03:16:22+08:00\n---\n\n## Notes\n",
                encoding="utf-8",
            )
            (topic_root / "log.md").write_text(
                "- 2026-10-10T03:16:00+08:00 | entity: [[general-defence-security|General Defence and "
                "Security]] | action: crawlStatus Completed -> Queued | crawlStatusAt: "
                "2026-10-09T19:16:00Z | reason: DAILY-2026-10-10 bulk-run exception | "
                "source: scripts/end_topic_crawl.md\n"
                "- 2026-10-10T03:16:00+08:00 | entity: [[general-defence-security|General Defence and "
                "Security]] | action: crawlStatus Queued -> In progress | crawlStatusAt: "
                "2026-10-09T19:16:01Z | reason: DAILY-2026-10-10 bulk-run exception | "
                "source: scripts/end_topic_crawl.md\n"
                "- 2026-10-10T03:16:00+08:00 | entity: [[general-defence-security|General Defence and "
                "Security]] | action: crawlStatus In progress -> Completed | crawlStatusAt: "
                "2026-10-09T19:16:02Z | reason: DAILY-2026-10-10 bulk-run exception | "
                "source: scripts/end_topic_crawl.md\n",
                encoding="utf-8",
            )
            original_log, original_dir = BUILDER.LOG, BUILDER.TOPIC_DIR
            try:
                BUILDER.LOG = topic_root / "log.md"
                BUILDER.TOPIC_DIR = topic_root
                episodes, _coverage = BUILDER.parse_log()
                eps = episodes.get("general-defence-security")
                self.assertEqual(len(eps), 1)
                self.assertEqual(eps[0]["result"], "Completed")
                self.assertEqual(eps[0]["note"], "DAILY-2026-10-10 bulk-run exception")
            finally:
                BUILDER.LOG, BUILDER.TOPIC_DIR = original_log, original_dir

    def test_older_verb_style_action_lines_still_parse(self):
        with tempfile.TemporaryDirectory() as temporary:
            topic_root = pathlib.Path(temporary)
            (topic_root / "log.md").write_text(
                "- 2026-09-18T03:55:00+08:00 | entity: [[air-capabilities|Air Capabilities]] | "
                "action: crawl started | reason: DAILY-2026-09-18 topic crawl plan run\n"
                "- 2026-09-18T04:10:00+08:00 | entity: [[air-capabilities|Air Capabilities]] | "
                "action: crawl completed | reason: DAILY-2026-09-18 crawl complete, 2 accepted\n",
                encoding="utf-8",
            )
            original_log = BUILDER.LOG
            try:
                BUILDER.LOG = topic_root / "log.md"
                episodes, _coverage = BUILDER.parse_log()
                eps = episodes.get("air-capabilities")
                self.assertEqual(len(eps), 1)
                self.assertEqual(eps[0]["result"], "Completed")
                self.assertEqual(eps[0]["accepted"], "2")
            finally:
                BUILDER.LOG = original_log


if __name__ == "__main__":
    unittest.main()
