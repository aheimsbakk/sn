import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from grc.manifest import load_manifest, save_manifest, update_episode_manifest


class ManifestTests(unittest.TestCase):
    def test_manifest_round_trip(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest = load_manifest(root)
            update_episode_manifest(
                manifest,
                episode=9,
                title_slug="episode-nine",
                transcript_url="https://example.com/sn-0009.txt",
                source_format="txt",
                original_encoding="utf-8",
                local_path="transcripts/sn-0009-episode-nine.md",
                source_sha="abc",
                status="present",
            )
            save_manifest(root, manifest)
            reloaded = load_manifest(root)
            self.assertEqual(reloaded["episodes"]["9"]["status"], "present")
            self.assertEqual(reloaded["episodes"]["9"]["source_sha"], "abc")
