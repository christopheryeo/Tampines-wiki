import unittest

from scripts.local_issue_radar_review import primary_review, second_review
from scripts.review_issue_radar_run import cluster_flags, make_outputs


def flag(tag, score, article_ids, tier="HOT"):
    return {
        "tag": tag,
        "tier": tier,
        "score": score,
        "recentVolume": len(article_ids),
        "recentArticleIds": article_ids,
        "articleIds": article_ids,
        "signals": {},
        "reasons": ["test"],
    }


class ReviewClusteringTests(unittest.TestCase):
    def test_non_transitive_clustering_prevents_bridge_snowball(self):
        clusters = cluster_flags([
            flag("seed", 0.90, [1, 2, 3, 4]),
            flag("near-seed", 0.80, [1, 2, 3]),
            flag("bridge-only", 0.70, [2, 3, 5, 6]),
        ])
        self.assertEqual(
            [member["flag"]["tag"] for member in clusters[0]["members"]],
            ["seed", "near-seed"],
        )
        self.assertEqual(clusters[1]["seedTag"], "bridge-only")

    def test_facilitated_repeat_is_not_alerted(self):
        metrics = {
            "domesticEvidence": True,
            "forcedResponderEvidence": True,
            "faultLineEvidence": True,
            "facilitatedShare": 0.8,
            "unfacilitatedShare": 0.2,
            "opinionatedShare": 0.0,
            "largestExactTitleShare": 0.7,
        }
        self.assertEqual(primary_review(metrics)["disposition"], "dismiss")

    def test_second_pass_requires_forced_responder_and_fault_line(self):
        metrics = {
            "domesticEvidence": True,
            "forcedResponderEvidence": False,
            "faultLineEvidence": True,
            "facilitatedShare": 0.0,
            "unfacilitatedShare": 1.0,
            "opinionatedShare": 1.0,
            "largestExactTitleShare": 0.2,
        }
        primary = primary_review(metrics)
        self.assertEqual(primary["disposition"], "quiet-watch")
        self.assertEqual(second_review(metrics, primary)["disposition"], "dismiss")

    def test_review_pack_includes_event_family_and_coherence_evidence(self):
        radar = {"source": {}, "asOf": "2026-09-20", "flags": [{
            **flag("example", 0.8, [1]), "recentEventFamilyIds": ["2026-09-20:example"],
        }]}
        indexed = {1: {
            "articleId": 1, "title": "Example", "publishedDate": "2026-09-20",
            "category": "", "tone": "", "eventType": "", "tags": [], "outlets": [],
            "countries": [], "summary": "", "path": "example.md",
            "relatedEntities": ["topic/example", "people/example"],
            "canonicalTopics": ["topic/example"],
        }}
        pack, _ = make_outputs(radar, indexed)
        cluster = pack["clusters"][0]
        self.assertEqual(cluster["eventFamilyCount"], 1)
        self.assertEqual(cluster["coherenceStatus"], "evidence-ready")
        self.assertIn("sharedEntities", cluster)
        self.assertIn("sharedCanonicalTopics", cluster)


if __name__ == "__main__":
    unittest.main()
