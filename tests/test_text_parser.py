import unittest

from sn.text_parser import parse_text_transcript


SAMPLE_TEXT = """SERIES: Security Now!
EPISODE: 1074
DATE: 2026-04-14
TITLE: What Mythos Means
HOSTS: Steve Gibson, Leo Laporte
SOURCE: https://media.grc.com/sn/sn-1074.mp3
DESCRIPTION: Example description.
SHOW TEASE: Example tease.

Leo Laporte: Welcome back.
Steve Gibson: Hello.

Copyright 2026 GRC
Creative Commons Attribution.
"""


class TextParserTests(unittest.TestCase):
    def test_parses_header_aliases_and_license(self) -> None:
        record = parse_text_transcript(
            SAMPLE_TEXT, transcript_url="https://example.com/sn-1074.txt"
        )
        self.assertEqual(record.episode, 1074)
        self.assertEqual(record.title, "What Mythos Means")
        self.assertEqual(record.speakers, ["Steve Gibson", "Leo Laporte"])
        self.assertEqual(record.show_tease, "Example tease.")
        self.assertIn("Creative Commons", record.license or "")
        self.assertEqual(record.transcript_lines[0], "**Leo Laporte:** Welcome back.")
