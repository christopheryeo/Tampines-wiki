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
    def test_coverage_heading_corruption_fails_cli_gate(self):
        for text in ("## Coverage- [[example|Example]]\n", "## Coverage\n\n## Coverage\n"):
            with self.subTest(text=text), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                note = root / "entities" / "people" / "example.md"
                note.parent.mkdir(parents=True)
                note.write_text(text)
                output = io.StringIO()
                with mock.patch.object(MODULE, "ROOT", str(root)), mock.patch.object(
                    sys, "argv", ["check_links.py", "--no-run-log", "--no-unlinked"]
                ), contextlib.redirect_stdout(output):
                    with self.assertRaises(SystemExit) as result:
                        MODULE.main()
                self.assertEqual(result.exception.code, 1)
                self.assertIn("INVALID COVERAGE HEADINGS", output.getvalue())

    def test_skips_runtime_dependencies_and_run_artifacts(self):
        self.assertTrue(MODULE.is_doc_file("issue-radar-site/node_modules/pkg/readme.md"))
        self.assertTrue(MODULE.is_doc_file("runs/2026-09-04/artifacts/report.md"))
        self.assertFalse(MODULE.is_doc_file("entities/article/2026-09/example.md"))

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

    def test_run_artifact_yaml_is_excluded_before_frontmatter_parsing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            article = root / "entities" / "article" / "2026-09" / "example.md"
            article.parent.mkdir(parents=True)
            article.write_text("---\nsourceId: '1'\n---\n\nNo links.\n", encoding="utf-8")
            artifact = root / "runs" / "2026-09-04" / "bad.md"
            artifact.parent.mkdir(parents=True)
            artifact.write_bytes(b"---\nvalue: \x88\n---\n")

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
            self.assertNotIn("YAML ERRORS", output.getvalue())


if __name__ == "__main__":
    unittest.main()
