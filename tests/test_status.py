import json
import unittest

from sn.status import (
    list_non_present,
    render_status_json,
    render_status_text,
    summarize_archive_state,
)


ARCHIVE_STATE = {
    "episodes": {
        "1": {
            "episode": 1,
            "status": "present",
            "local_path": "sn-0001.md",
        },
        "2": {"episode": 2, "status": "remote_missing", "last_error_summary": "404"},
        "3": {"episode": 3, "status": "parse_error", "last_error_summary": "bad html"},
    }
}


class StatusTests(unittest.TestCase):
    def test_summarize_archive_state(self) -> None:
        summary = summarize_archive_state(ARCHIVE_STATE)
        self.assertEqual(summary["present"], 1)
        self.assertEqual(summary["remote_missing"], 1)
        self.assertEqual(summary["parse_error"], 1)

    def test_renderers_include_missing_items(self) -> None:
        summary = summarize_archive_state(ARCHIVE_STATE)
        missing = list_non_present(ARCHIVE_STATE)
        text_output = render_status_text(summary, missing)
        json_output = render_status_json(summary, missing)
        self.assertIn("episode 2: remote_missing - 404", text_output)
        self.assertEqual(len(json.loads(json_output)["episodes"]), 2)
