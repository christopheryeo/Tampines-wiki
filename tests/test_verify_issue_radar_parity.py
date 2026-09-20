import json
import pathlib
import subprocess
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "verify_issue_radar_parity.py"


class IssueRadarParityTests(unittest.TestCase):
    def run_check(self, uat, markdown):
        with tempfile.TemporaryDirectory() as folder:
            folder = pathlib.Path(folder)
            uat_path, markdown_path, output = folder / "uat.json", folder / "markdown.json", folder / "out.json"
            uat_path.write_text(json.dumps(uat), encoding="utf-8")
            markdown_path.write_text(json.dumps(markdown), encoding="utf-8")
            result = subprocess.run([
                sys.executable, str(SCRIPT), "--uat-manifest", str(uat_path),
                "--markdown-manifest", str(markdown_path), "--output", str(output),
            ], capture_output=True, text=True)
            return result.returncode, json.loads(output.read_text(encoding="utf-8"))

    def test_accepts_case_insensitive_exact_parity(self):
        uat = {"asOf": "2026-09-20", "articles": [{
            "articleId": 7, "publishedDate": "2026-09-20", "tags": ["Example"],
            "outlets": ["CNA"], "countries": ["Singapore"],
        }]}
        markdown = {"asOf": "2026-09-20", "articles": [{
            "articleId": 7, "publishedDate": "2026-09-20T00:00:00", "tags": ["example"],
            "outlets": ["cna"], "countries": ["singapore"],
        }]}
        code, report = self.run_check(uat, markdown)
        self.assertEqual(code, 0)
        self.assertEqual(report["result"], "PASS")

    def test_rejects_tag_or_coverage_drift(self):
        uat = {"asOf": "2026-09-20", "articles": [{
            "articleId": 7, "publishedDate": "2026-09-20", "tags": ["example"],
            "outlets": ["CNA"], "countries": ["Singapore"],
        }]}
        markdown = {"asOf": "2026-09-20", "articles": [{
            "articleId": 7, "publishedDate": "2026-09-20", "tags": ["other"],
            "outlets": ["CNA"], "countries": ["Singapore"],
        }]}
        code, report = self.run_check(uat, markdown)
        self.assertEqual(code, 1)
        self.assertEqual(report["failureCount"], 1)


if __name__ == "__main__":
    unittest.main()
