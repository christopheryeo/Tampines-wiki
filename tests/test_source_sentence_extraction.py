"""Source-derived sentence fragments found by the wiki quality audit."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from ingest_cascade import excerpt, key_points, source_sentences


class SourceSentenceTests(unittest.TestCase):
    def test_titles_initials_and_dates_stay_with_their_sentence(self):
        text = "The statement followed the acquittal of Sgt. Kevin MacIntyre on Sept. 27. Donald J. Trump discussed NASA with advisers."
        self.assertEqual(source_sentences(text), [
            "The statement followed the acquittal of Sgt. Kevin MacIntyre on Sept. 27.",
            "Donald J. Trump discussed NASA with advisers.",
        ])
        self.assertEqual(key_points(text)[0], source_sentences(text)[0])

    def test_truncation_is_explicit_and_does_not_split_a_word(self):
        self.assertEqual(excerpt("Complete sentence.", 30), "Complete sentence.")
        result = excerpt("one two extraordinarilylongword another", 18)
        self.assertEqual(result, "one two…")


if __name__ == "__main__":
    unittest.main()
