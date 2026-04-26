import json
import unittest

from grc.status import (
    list_non_present,
    render_status_json,
    render_status_text,
    summarize_manifest,
)


MANIFEST = {
    "episodes": {
        "1": {
            "episode": 1,
            "status": "present",
            "local_path": "transcripts/sn-0001.md",
        },
        "2": {"episode": 2, "status": "remote_missing", "last_error_summary": "404"},
        "3": {"episode": 3, "status": "parse_error", "last_error_summary": "bad html"},
    }
}


class StatusTests(unittest.TestCase):
    def test_summarize_manifest(self) -> None:
        summary = summarize_manifest(MANIFEST)
        self.assertEqual(summary["present"], 1)
        self.assertEqual(summary["remote_missing"], 1)
        self.assertEqual(summary["parse_error"], 1)

    def test_renderers_include_missing_items(self) -> None:
        summary = summarize_manifest(MANIFEST)
        missing = list_non_present(MANIFEST)
        text_output = render_status_text(summary, missing)
        json_output = render_status_json(summary, missing)
        self.assertIn("episode 2: remote_missing - 404", text_output)
        self.assertEqual(len(json.loads(json_output)["episodes"]), 2)
