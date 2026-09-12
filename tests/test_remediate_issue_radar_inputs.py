import importlib.util
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location(
    "remediate_issue_radar_inputs",
    ROOT / "scripts" / "remediate_issue_radar_inputs.py",
)
REMEDIATION = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = REMEDIATION
spec.loader.exec_module(REMEDIATION)


class IssueRadarInputRemediationTests(unittest.TestCase):
    def test_issue_tag_section_is_inserted_before_projection(self):
        body = "## Summary\nSaved evidence.\n\n## Database Projection\n```json\n{}\n```"
        rendered = REMEDIATION.replace_issue_tags(body, ["Aircraft"])
        self.assertIn("## Issue Tags\n- [[tag/aircraft|Aircraft]]", rendered)
        self.assertLess(rendered.index("## Issue Tags"), rendered.index("## Database Projection"))

    def test_issue_tag_section_is_replaced_idempotently(self):
        body = "## Issue Tags\n- Old\n\n## AI Context\nSaved."
        once = REMEDIATION.replace_issue_tags(body, ["Aircraft"])
        twice = REMEDIATION.replace_issue_tags(once, ["Aircraft"])
        self.assertEqual(once, twice)
        self.assertNotIn("- Old", once)

    def test_defect_keys_distinguish_coverage_rows(self):
        self.assertNotEqual(
            REMEDIATION.defect_key("1", "coverage.country", 0),
            REMEDIATION.defect_key("1", "coverage.country", 1),
        )

    def test_only_coverage_fields_can_be_reviewed_exceptions(self):
        self.assertEqual(
            REMEDIATION.EXCEPTION_FIELDS,
            {"coverage.country", "coverage.mediaOutletCategory"},
        )
        self.assertTrue(REMEDIATION.MANDATORY.isdisjoint(REMEDIATION.EXCEPTION_FIELDS))


if __name__ == "__main__":
    unittest.main()
