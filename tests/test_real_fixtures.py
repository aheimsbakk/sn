import unittest
from pathlib import Path

from sn.archive_index import parse_archive_entries
from sn.html_parser import parse_html_transcript
from sn.normalize import detect_and_decode
from sn.text_parser import parse_text_transcript


FIXTURES = Path(__file__).parent / "fixtures"


class RealFixtureTests(unittest.TestCase):
    def test_real_archive_index_contains_expected_episodes(self) -> None:
        archive_text = (FIXTURES / "archive" / "securitynow-main.htm").read_text(
            encoding="utf-8", errors="replace"
        )
        entries = parse_archive_entries(
            "https://www.grc.com/securitynow.htm", archive_text
        )
        entries_by_episode = {entry.episode: entry for entry in entries}

        self.assertIn(1074, entries_by_episode)
        self.assertIn(1075, entries_by_episode)
        self.assertEqual(entries_by_episode[1074].title, "Episode 1074")
        self.assertEqual(
            entries_by_episode[1074].transcript_txt_url,
            "https://www.grc.com/sn/sn-1074.txt",
        )
        self.assertIsNone(entries_by_episode[1075].transcript_txt_url)

    def test_real_recent_text_transcript_parses(self) -> None:
        payload = (FIXTURES / "transcripts" / "sn-1074.txt").read_bytes()
        text, encoding = detect_and_decode(payload)
        record = parse_text_transcript(
            text,
            transcript_url="https://www.grc.com/sn/sn-1074.txt",
            original_encoding=encoding,
        )

        self.assertEqual(record.episode, 1074)
        self.assertEqual(record.title, "What Mythos Means")
        self.assertEqual(record.published, "April 14, 2026")
        self.assertEqual(record.speakers, ["Steve Gibson", "Leo Laporte"])
        self.assertTrue(
            record.show_tease
            and record.show_tease.startswith("It's time for Security Now!")
        )
        self.assertEqual(record.audio_url, "https://media.grc.com/sn/sn-1074.mp3")
        self.assertTrue(record.transcript_lines[0].startswith("**LEO LAPORTE:**"))

    def test_real_milestone_text_transcript_parses(self) -> None:
        payload = (FIXTURES / "transcripts" / "sn-1000.txt").read_bytes()
        text, encoding = detect_and_decode(payload)
        record = parse_text_transcript(
            text,
            transcript_url="https://www.grc.com/sn/sn-1000.txt",
            original_encoding=encoding,
        )

        self.assertEqual(record.episode, 1000)
        self.assertEqual(record.title, "One Thousand!")
        self.assertEqual(record.published, "November 12, 2024")
        self.assertIn("Bitwarden", record.description or "")
        self.assertEqual(record.speakers, ["Steve Gibson", "Leo Laporte"])

    def test_real_recent_html_transcript_parses(self) -> None:
        html_text = (FIXTURES / "transcripts" / "sn-1074.htm").read_text(
            encoding="utf-8", errors="replace"
        )
        record = parse_html_transcript(
            html_text, transcript_url="https://www.grc.com/sn/sn-1074.htm"
        )

        self.assertEqual(record.episode, 1074)
        self.assertEqual(record.title, "What Mythos Means")
        self.assertIn("Anthropic", record.description or "")
        self.assertEqual(record.audio_url, "http://media.GRC.com/sn/SN-1074.mp3")
        self.assertTrue(
            record.show_tease and "too dangerous to release" in record.show_tease
        )
        self.assertTrue(record.transcript_lines[0].startswith("**Leo Laporte:**"))

    def test_real_milestone_html_transcript_parses(self) -> None:
        html_text = (FIXTURES / "transcripts" / "sn-1000.htm").read_text(
            encoding="utf-8", errors="replace"
        )
        record = parse_html_transcript(
            html_text, transcript_url="https://www.grc.com/sn/sn-1000.htm"
        )

        self.assertEqual(record.episode, 1000)
        self.assertEqual(record.title, "One Thousand!")
        self.assertIn("Bitwarden", record.description or "")
        self.assertEqual(record.audio_url, "http://media.GRC.com/sn/SN-1000.mp3")
        self.assertTrue(record.transcript_lines[1].startswith("**Steve Gibson:**"))
