import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from sn.archive_state import load_archive_state


class ArchiveStateTests(unittest.TestCase):
    def test_load_archive_state_reads_front_matter_from_flat_files(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "sn-0009-episode-nine.md").write_text(
                "---\n"
                "series: Security Now!\n"
                "episode: 9\n"
                "title: Episode Nine\n"
                "transcript_url: https://example.com/sn-0009.txt\n"
                "source_format: txt\n"
                "original_encoding: utf-8\n"
                "source_sha: abc\n"
                "---\n\n"
                "# Security Now! Episode 9: Episode Nine\n",
                encoding="utf-8",
            )

            archive_state = load_archive_state(root)

            self.assertEqual(archive_state["episodes"]["9"]["status"], "present")
            self.assertEqual(
                archive_state["episodes"]["9"]["local_path"], "sn-0009-episode-nine.md"
            )
            self.assertEqual(archive_state["episodes"]["9"]["source_sha"], "abc")

    def test_load_archive_state_ignores_non_archive_markdown_files(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "README.md").write_text("# Not an episode\n", encoding="utf-8")

            archive_state = load_archive_state(root)

            self.assertEqual(archive_state, {"episodes": {}})
