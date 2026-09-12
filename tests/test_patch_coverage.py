"""Regression protection for Coverage headings and repeat patching."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import patch_coverage


class CoverageInsertionTests(unittest.TestCase):
    def test_first_bullet_preserves_heading_and_existing_unbulleted_link(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "people").mkdir()
            path = root / "people" / "example.md"
            original = "---\npersonId: example\nmentionCount: 1\n---\n\n## Coverage\n[[old-article|Existing evidence]]\n\n## Notes\nPreserve this prose.\n"
            path.write_text(original)
            updates = [{"article": "new-article", "label": "New evidence"}]
            with patch.object(patch_coverage, "ENTITIES_DIR", str(root)):
                preview = patch_coverage.apply_update("people", "example", updates, True)
                self.assertEqual(path.read_text(), original)
                self.assertEqual(preview["new_count"], 2)
                patch_coverage.apply_update("people", "example", updates, False)
                actual = path.read_text()
                self.assertIn("\n## Coverage\n", actual)
                self.assertIn("[[old-article|Existing evidence]]", actual)
                self.assertIn("\n## Notes\nPreserve this prose.\n", actual)
                block = patch_coverage.find_coverage_block(actual)
                self.assertIsNotNone(block)
                self.assertIn("[[new-article|New evidence]]", block[2])
                again = patch_coverage.apply_update("people", "example", updates, False)
                self.assertTrue(again["noop"])
                self.assertEqual(path.read_text(), actual)


if __name__ == "__main__":
    unittest.main()
