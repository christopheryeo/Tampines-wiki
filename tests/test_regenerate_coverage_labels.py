import importlib.util
from pathlib import Path
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "regenerate_coverage_labels.py"
SPEC = importlib.util.spec_from_file_location("regenerate_coverage_labels", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class RegenerateCoverageLabelsTests(unittest.TestCase):
    def test_repairs_bracketed_tag_label_from_article_summary(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            article = root / "entities" / "article" / "2026-08" / "article-one.md"
            article.parent.mkdir(parents=True)
            article.write_text(
                "## Summary\n[WATCH] [[outlet/example|Example]] reported the verified update. More detail.\n",
                encoding="utf-8",
            )
            tag = root / "entities" / "tag" / "example.md"
            tag.parent.mkdir(parents=True)
            tag.write_text(
                "## Coverage\n\n"
                "- [[article/2026-08/article-one|[WATCH] Example | Source]]\n",
                encoding="utf-8",
            )

            original_root = MODULE.ROOT
            MODULE.ROOT = root
            try:
                changed_links, changed_files, skipped = MODULE.regenerate(
                    dry_run=False, log=False, domains=("tag",)
                )
            finally:
                MODULE.ROOT = original_root

            self.assertEqual((changed_links, changed_files, skipped), (1, 1, []))
            self.assertIn(
                "- [[article/2026-08/article-one|WATCH Example reported the verified update.]]",
                tag.read_text(encoding="utf-8"),
            )

    def test_leaves_safe_label_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            article = root / "entities" / "article" / "2026-08" / "article-one.md"
            article.parent.mkdir(parents=True)
            article.write_text("## Summary\nA safe summary.\n", encoding="utf-8")
            tag = root / "entities" / "tag" / "example.md"
            tag.parent.mkdir(parents=True)
            original = "## Coverage\n\n- [[article/2026-08/article-one|Safe label]]\n"
            tag.write_text(original, encoding="utf-8")

            original_root = MODULE.ROOT
            MODULE.ROOT = root
            try:
                result = MODULE.regenerate(dry_run=False, log=False, domains=("tag",))
            finally:
                MODULE.ROOT = original_root

            self.assertEqual(result, (0, 0, []))
            self.assertEqual(tag.read_text(encoding="utf-8"), original)

    def test_log_records_every_repaired_source_for_one_entity(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            article_root = root / "entities" / "article" / "2026-08"
            article_root.mkdir(parents=True)
            for article_id in ("article-one", "article-two"):
                (article_root / f"{article_id}.md").write_text(
                    f"## Summary\n[{article_id}] verified summary.\n", encoding="utf-8"
                )
            tag_root = root / "entities" / "tag"
            tag_root.mkdir(parents=True)
            tag = tag_root / "example.md"
            tag.write_text(
                "## Coverage\n\n"
                "- [[article/2026-08/article-one|[ONE] first]]\n"
                "- [[article/2026-08/article-two|[TWO] second]]\n",
                encoding="utf-8",
            )
            (tag_root / "log.md").write_text("# Log\n", encoding="utf-8")

            original_root = MODULE.ROOT
            MODULE.ROOT = root
            try:
                result = MODULE.regenerate(dry_run=False, log=True, domains=("tag",))
            finally:
                MODULE.ROOT = original_root

            self.assertEqual(result, (2, 1, []))
            log = (tag_root / "log.md").read_text(encoding="utf-8")
            self.assertEqual(log.count("| entity: [[example]] |"), 1)
            self.assertIn("[[article/2026-08/article-one|article-one verified summary.]]", log)
            self.assertIn("[[article/2026-08/article-two|article-two verified summary.]]", log)


if __name__ == "__main__":
    unittest.main()
