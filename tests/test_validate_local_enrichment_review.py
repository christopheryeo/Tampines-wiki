import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate_local_enrichment_review.py"
if str(SCRIPT.parent) not in sys.path:
    sys.path.insert(0, str(SCRIPT.parent))
SPEC = importlib.util.spec_from_file_location("validate_local_enrichment_review", SCRIPT)
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


def classification(evidence="Literal saved evidence."):
    return {
        "tone": "Factual",
        "tone_confidence": 0.9,
        "tone_evidence": [evidence],
        "tone_sentiment": "Neutral",
        "sentiment_confidence": 0.9,
        "sentiment_evidence": [evidence],
        "event_type": "Unfacilitated",
        "event_confidence": 0.9,
        "event_trigger": "no clear organised trigger",
        "event_evidence": [evidence],
        "issue_tags": ["Active Tag"],
        "outlet_name": "Example News",
        "outlet_country": "",
        "institutional_category": "Non-institutional",
        "metadata_confidence": 0.9,
        "review_required": False,
        "review_reason": "",
    }


class LocalEnrichmentReviewValidatorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.input_root = self.root / "Inputs" / "articles"
        month = self.input_root / "2026-08"
        month.mkdir(parents=True)
        self.filename = "crawl-42-example.md"
        self.input_path = month / self.filename
        self.input_text = "---\narticleId: crawl-42\n---\nLiteral saved evidence.\n"
        self.input_path.write_text(self.input_text, encoding="utf-8")
        digest = hashlib.sha256(self.input_path.read_bytes()).hexdigest()
        self.eligible = self.root / "eligible.json"
        self.eligible.write_text(json.dumps({
            "articleCount": 1,
            "articles": [{
                "filename": self.filename,
                "articleId": "crawl-42",
                "sha256": digest,
            }],
        }), encoding="utf-8")
        self.routable = self.root / "routable.txt"
        self.routable.write_text(f"Inputs/articles/{self.filename}\n", encoding="utf-8")
        self.frozen = VALIDATOR.load_frozen_inputs(
            self.eligible,
            self.routable,
            root=self.root,
            input_root=self.input_root,
            expected_count=1,
        )

    def tearDown(self):
        self.temp.cleanup()

    def write_review(self, value):
        path = self.root / "review.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def payload(self, evidence="Literal saved evidence."):
        return {
            "schemaVersion": VALIDATOR.REVIEW_SCHEMA,
            "inputCount": 1,
            "assessedCount": 1,
            "assessments": [{
                "articleId": "crawl-42",
                "path": "Inputs/articles/2026-08/crawl-42-example.md",
                "inputSha256": self.frozen["crawl-42"]["sha256"],
                "classification": classification(evidence),
            }],
        }

    def test_accepts_complete_literal_evidence_review(self):
        path = self.write_review(self.payload())
        result = VALIDATOR.validate_review(path, self.frozen, active_tags={"Active Tag"})
        self.assertTrue(result["valid"])

    def test_rejects_nonliteral_evidence(self):
        path = self.write_review(self.payload("Paraphrased evidence."))
        with self.assertRaisesRegex(VALIDATOR.ValidationError, "not a literal substring"):
            VALIDATOR.validate_review(path, self.frozen, active_tags={"Active Tag"})

    def test_rejects_too_many_evidence_items(self):
        payload = self.payload()
        payload["assessments"][0]["classification"]["tone_evidence"] = [
            "Literal saved evidence.",
        ] * 4
        path = self.write_review(payload)
        with self.assertRaisesRegex(VALIDATOR.ValidationError, "maximum is 3"):
            VALIDATOR.validate_review(path, self.frozen, active_tags={"Active Tag"})

    def test_rejects_inactive_tag(self):
        path = self.write_review(self.payload())
        with self.assertRaisesRegex(VALIDATOR.ValidationError, "not active Tag entities"):
            VALIDATOR.validate_review(path, self.frozen, active_tags=set())

    def test_rejects_incomplete_artifact_coverage(self):
        payload = self.payload()
        payload["assessments"] = []
        path = self.write_review(payload)
        with self.assertRaisesRegex(VALIDATOR.ValidationError, "assessment list has 0 rows"):
            VALIDATOR.validate_review(path, self.frozen, active_tags={"Active Tag"})

    def test_rejects_invalid_enum_and_empty_required_text(self):
        payload = self.payload()
        payload["assessments"][0]["classification"]["tone"] = "Mixed"
        path = self.write_review(payload)
        with self.assertRaisesRegex(VALIDATOR.ValidationError, "invalid tone"):
            VALIDATOR.validate_review(path, self.frozen, active_tags={"Active Tag"})

        payload = self.payload()
        payload["assessments"][0]["classification"]["event_trigger"] = ""
        path = self.write_review(payload)
        with self.assertRaisesRegex(VALIDATOR.ValidationError, "event_trigger must be non-empty"):
            VALIDATOR.validate_review(path, self.frozen, active_tags={"Active Tag"})

    def test_rejects_changed_routed_input_hash(self):
        self.input_path.write_text(self.input_text + "changed", encoding="utf-8")
        with self.assertRaisesRegex(VALIDATOR.ValidationError, "does not match frozen"):
            VALIDATOR.load_frozen_inputs(
                self.eligible,
                self.routable,
                root=self.root,
                input_root=self.input_root,
                expected_count=1,
            )


if __name__ == "__main__":
    unittest.main()
