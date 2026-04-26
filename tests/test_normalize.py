import unittest

from grc.normalize import detect_and_decode, normalize_speaker_line, slugify


class NormalizeTests(unittest.TestCase):
    def test_detect_and_decode_falls_back_to_cp1252(self) -> None:
        text, encoding = detect_and_decode(b"caf\xe9")
        self.assertEqual(text, "café")
        self.assertEqual(encoding, "cp1252")

    def test_slugify_limits_length(self) -> None:
        slug = slugify("What Mythos Means And Why It Matters More Than Expected")
        self.assertLessEqual(len(slug), 32)
        self.assertEqual(slug, "what-mythos-means-and-why-it-mat")

    def test_normalize_speaker_line_formats_label(self) -> None:
        self.assertEqual(
            normalize_speaker_line("Steve Gibson: Hello there"),
            "**Steve Gibson:** Hello there",
        )
