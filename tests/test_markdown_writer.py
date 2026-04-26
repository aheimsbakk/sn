import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from sn.markdown_writer import build_markdown, write_markdown
from sn.models import TranscriptRecord


class MarkdownWriterTests(unittest.TestCase):
    def test_build_markdown_contains_front_matter_and_body(self) -> None:
        record = TranscriptRecord(
            series="Security Now!",
            episode=7,
            title="Lucky Seven",
            published="2026-01-01",
            speakers=["Steve Gibson"],
            description="A test episode.",
            audio_url="https://example.com/audio.mp3",
            transcript_url="https://example.com/sn-0007.txt",
            source_format="txt",
            original_encoding="utf-8",
            source_sha="abc123",
            license="Copyright text.",
            show_tease="A teaser.",
            transcript_lines=["**Steve Gibson:** Hello"],
        )
        output = build_markdown(record)
        self.assertIn("episode: 7", output)
        self.assertIn("source_sha: abc123", output)
        self.assertIn("## Transcript", output)
        self.assertIn("**Steve Gibson:** Hello", output)

    def test_write_markdown_uses_expected_path(self) -> None:
        record = TranscriptRecord(
            series="Security Now!", episode=7, title="Lucky Seven", published=None
        )
        with TemporaryDirectory() as temp_dir:
            path = write_markdown(Path(temp_dir), record)
            self.assertEqual(path.parent, Path(temp_dir))
            self.assertTrue(path.name.startswith("sn-0007-lucky-seven"))
            self.assertTrue(path.exists())
