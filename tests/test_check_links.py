import contextlib
import importlib.util
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_links.py"
sys.path.insert(0, str(SCRIPT.parent))
SPEC = importlib.util.spec_from_file_location("check_links", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class FindUnlinkedEntitiesTests(unittest.TestCase):
    def test_preserves_link_and_word_boundary_semantics(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            article = root / "entities" / "article" / "2026-08" / "example.md"
            article.parent.mkdir(parents=True)
            article.write_text(
                "## Summary\n"
                "Alpha Agency met Beta Group while RUSSIA was discussed.\n\n"
                "## Key Points\n"
                "- [[organisations/alpha-agency|Alpha Agency]] attended.\n",
                encoding="utf-8",
            )
            names = {
                "Alpha Agency": {"alpha-agency"},
                "Beta Group": {"beta-group"},
                "US": {"united-states"},
            }

            original_root = MODULE.ROOT
            MODULE.ROOT = str(root)
            try:
                findings = MODULE.find_unlinked_entities(
                    ["entities/article/2026-08/example.md"], names
                )
            finally:
                MODULE.ROOT = original_root

            self.assertEqual(
                findings,
                [("entities/article/2026-08/example.md", "Beta Group", "beta-group")],
            )

    def test_unmatched_literal_closer_is_not_reported_as_coverage_corruption(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            article = root / "entities" / "article" / "2026-08" / "example.md"
            article.parent.mkdir(parents=True)
            article.write_text("## Summary\nPreserved source text ends here. ]]\n", encoding="utf-8")

            original_root = MODULE.ROOT
            MODULE.ROOT = str(root)
            output = io.StringIO()
            try:
                with mock.patch.object(
                    sys, "argv", ["check_links.py", "--no-run-log", "--no-unlinked"]
                ), contextlib.redirect_stdout(output):
                    with self.assertRaises(SystemExit) as exit_context:
                        MODULE.main()
            finally:
                MODULE.ROOT = original_root

            self.assertEqual(exit_context.exception.code, 0)
            rendered = output.getvalue()
            self.assertIn("UNBALANCED WIKILINK BRACKETS (1 note", rendered)
            self.assertNotIn("MALFORMED COVERAGE LABELS", rendered)


if __name__ == "__main__":
    unittest.main()
