import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from grc.http import FetchError, RemoteMissingError
from grc.models import EpisodeIndexEntry, FetchResult
from grc.sync import (
    discover_episode_entries,
    fetch_and_parse_entry,
    plan_sync,
    sync_archive,
)


MAIN_URL = "https://www.grc.com/securitynow.htm"
YEAR_URL = "https://www.grc.com/securitynow2025.htm"
TXT_URL = "https://www.grc.com/sn/sn-1074.txt"
HTML_URL = "https://www.grc.com/sn/sn-1074.htm"


class FakeClient:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def fetch(self, url: str):
        self.calls.append(url)
        response = self.responses[url]
        if isinstance(response, Exception):
            raise response
        return response


def _result(url: str, text: str) -> FetchResult:
    return FetchResult(
        url=url,
        status_code=200,
        data=text.encode("utf-8"),
        content_type="text/html",
        charset="utf-8",
    )


class SyncTests(unittest.TestCase):
    def test_discover_episode_entries_combines_pages(self) -> None:
        client = FakeClient(
            {
                MAIN_URL: _result(
                    MAIN_URL,
                    '<a href="securitynow2025.htm">2025</a><a href="sn/sn-1074.txt">SN 1074 transcript</a>',
                ),
                YEAR_URL: _result(
                    YEAR_URL, '<a href="sn/sn-1074.htm">SN 1074 html</a>'
                ),
            }
        )
        entries = discover_episode_entries(client)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].episode, 1074)
        self.assertEqual(entries[0].transcript_html_url, HTML_URL)

    def test_fetch_and_parse_falls_back_to_html(self) -> None:
        entry = EpisodeIndexEntry(
            episode=1074,
            title="What Mythos Means",
            transcript_txt_url=TXT_URL,
            transcript_html_url=HTML_URL,
        )
        client = FakeClient(
            {
                TXT_URL: _result(TXT_URL, "not a valid transcript header"),
                HTML_URL: _result(
                    HTML_URL,
                    "<html><head><title>Security Now! Episode 1074 - What Mythos Means</title></head><body><p>Leo Laporte: Hello</p></body></html>",
                ),
            }
        )
        record, _ = fetch_and_parse_entry(client, entry, "auto")
        self.assertEqual(record.source_format, "html")
        self.assertEqual(record.episode, 1074)

    def test_plan_sync_skips_present_existing_files(self) -> None:
        entry = EpisodeIndexEntry(episode=1074, title="What Mythos Means")
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            transcript_dir = root / "transcripts"
            transcript_dir.mkdir()
            existing_file = transcript_dir / "sn-1074-what-mythos-means.md"
            existing_file.write_text("ok", encoding="utf-8")
            manifest = {"episodes": {"1074": {"status": "present"}}}
            plan = plan_sync(
                [entry],
                manifest,
                root,
                force=False,
                from_episode=None,
                to_episode=None,
                latest=None,
            )
            self.assertEqual(plan.to_fetch, [])
            self.assertEqual(plan.skipped_existing, [1074])

    def test_sync_archive_returns_partial_when_missing(self) -> None:
        class MissingClient(FakeClient):
            pass

        client = MissingClient(
            {
                MAIN_URL: _result(
                    MAIN_URL, '<a href="sn/sn-1074.txt">SN 1074 transcript</a>'
                ),
                TXT_URL: RemoteMissingError(TXT_URL, "missing transcript"),
            }
        )
        with TemporaryDirectory() as temp_dir:
            exit_code, manifest = sync_archive(Path(temp_dir), client=client)
            self.assertEqual(exit_code, 2)
            self.assertEqual(manifest["episodes"]["1074"]["status"], "remote_missing")
