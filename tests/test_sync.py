import io
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from grc.archive_state import load_archive_state
from grc.http import FetchError, RemoteMissingError
from grc.models import EpisodeIndexEntry, FetchResult, RemoteMetadata
from grc.sync import (
    discover_episode_entries,
    fetch_and_parse_entry,
    plan_sync,
    sync_archive,
)


MAIN_URL = "https://www.grc.com/securitynow.htm"
YEAR_URL = "https://www.grc.com/sn/past/2025.htm"
YEAR_2005_URL = "https://www.grc.com/sn/past/2005.htm"
TXT_URL = "https://www.grc.com/sn/sn-1074.txt"
HTML_URL = "https://www.grc.com/sn/sn-1074.htm"


class FakeClient:
    def __init__(self, responses, metadata_responses=None):
        self.responses = responses
        self.metadata_responses = metadata_responses or {}
        self.calls = []
        self.metadata_calls = []

    def fetch(self, url: str):
        self.calls.append(url)
        response = self.responses[url]
        if isinstance(response, BaseException):
            raise response
        return response

    def fetch_metadata(self, url: str):
        self.metadata_calls.append(url)
        response = self.metadata_responses[url]
        if isinstance(response, BaseException):
            raise response
        return response


def _result(
    url: str,
    text: str,
    *,
    etag: str | None = '"etag-1"',
    last_modified: str | None = "Sat, 26 Apr 2026 12:00:00 GMT",
) -> FetchResult:
    return FetchResult(
        url=url,
        status_code=200,
        data=text.encode("utf-8"),
        content_type="text/html",
        charset="utf-8",
        etag=etag,
        last_modified=last_modified,
        content_length=len(text.encode("utf-8")),
    )


def _metadata(
    url: str,
    *,
    etag: str | None = '"etag-1"',
    last_modified: str | None = "Sat, 26 Apr 2026 12:00:00 GMT",
    content_length: int = 83,
) -> RemoteMetadata:
    return RemoteMetadata(
        url=url,
        status_code=200,
        content_type="text/plain",
        charset="utf-8",
        etag=etag,
        last_modified=last_modified,
        content_length=content_length,
    )


class SyncTests(unittest.TestCase):
    def test_sync_archive_emits_verbose_fetch_progress(self) -> None:
        client = FakeClient(
            {
                MAIN_URL: _result(
                    MAIN_URL, '<a href="sn/sn-1074.txt">SN 1074 transcript</a>'
                ),
                TXT_URL: _result(
                    TXT_URL,
                    "SERIES: Security Now!\nEPISODE: 1074\nTITLE: What Mythos Means\n\nLeo Laporte: Hello",
                ),
            }
        )
        with TemporaryDirectory() as temp_dir:
            buffer = io.StringIO()
            exit_code, _ = sync_archive(
                Path(temp_dir), client=client, verbose=1, output=buffer
            )
        self.assertEqual(exit_code, 0)
        self.assertIn(f"fetch archive index: {MAIN_URL}", buffer.getvalue())
        self.assertIn(f"fetch transcript txt: {TXT_URL}", buffer.getvalue())

    def test_discover_episode_entries_combines_pages(self) -> None:
        client = FakeClient(
            {
                MAIN_URL: _result(
                    MAIN_URL,
                    '<a href="/sn/past/2025.htm">2025</a><a href="sn/sn-1074.txt">SN 1074 transcript</a>',
                ),
                YEAR_URL: _result(
                    YEAR_URL, '<a href="/sn/sn-1074.htm">SN 1074 html</a>'
                ),
            }
        )
        entries = discover_episode_entries(client)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].episode, 1074)
        self.assertEqual(entries[0].transcript_html_url, HTML_URL)

    def test_discover_episode_entries_fetches_old_yearly_archives(self) -> None:
        old_txt_url = "https://www.grc.com/sn/sn-0010.txt"
        client = FakeClient(
            {
                MAIN_URL: _result(MAIN_URL, '<a href="/sn/past/2005.htm">2005</a>'),
                YEAR_2005_URL: _result(
                    YEAR_2005_URL, '<a href="/sn/sn-0010.txt">SN 10 transcript</a>'
                ),
            }
        )

        entries = discover_episode_entries(client)

        self.assertEqual([entry.episode for entry in entries], [10])
        self.assertEqual(entries[0].transcript_txt_url, old_txt_url)
        self.assertEqual(client.calls, [MAIN_URL, YEAR_2005_URL])

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
            existing_file = root / "sn-1074-what-mythos-means.md"
            existing_file.write_text(
                "---\nepisode: 1074\ntitle: What Mythos Means\nsource_sha: abc\n---\n",
                encoding="utf-8",
            )
            archive_state = load_archive_state(root)
            plan = plan_sync(
                [entry],
                archive_state,
                root,
                force=False,
                year=None,
                latest=None,
            )
            self.assertEqual(plan.to_fetch, [])
            self.assertEqual(plan.skipped_existing, [1074])

    def test_plan_sync_filters_to_selected_year(self) -> None:
        entries = [
            EpisodeIndexEntry(episode=10, title="Episode 10", published="2005-08-11"),
            EpisodeIndexEntry(
                episode=1074, title="Episode 1074", published="2026-04-14"
            ),
        ]

        plan = plan_sync(
            entries,
            {"episodes": {}},
            Path("/tmp/archive"),
            force=False,
            year=2005,
            latest=None,
        )

        self.assertEqual([entry.episode for entry in plan.to_fetch], [10])

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
            exit_code, archive_state = sync_archive(Path(temp_dir), client=client)
            self.assertEqual(exit_code, 2)
            self.assertEqual(
                archive_state["episodes"]["1074"]["status"], "remote_missing"
            )

    def test_sync_archive_saves_completed_work_before_interrupt(self) -> None:
        next_txt_url = "https://www.grc.com/sn/sn-1075.txt"
        client = FakeClient(
            {
                MAIN_URL: _result(
                    MAIN_URL,
                    '<a href="sn/sn-1074.txt">SN 1074 transcript</a><a href="sn/sn-1075.txt">SN 1075 transcript</a>',
                ),
                TXT_URL: _result(
                    TXT_URL,
                    "SERIES: Security Now!\nEPISODE: 1074\nTITLE: What Mythos Means\n\nLeo Laporte: Hello",
                ),
                next_txt_url: KeyboardInterrupt(),
            }
        )
        with TemporaryDirectory() as temp_dir:
            with self.assertRaises(KeyboardInterrupt):
                sync_archive(Path(temp_dir), client=client)
            archive_state = load_archive_state(Path(temp_dir))
        self.assertEqual(archive_state["episodes"]["1074"]["status"], "present")

    def test_force_sync_skips_download_when_metadata_sha_matches(self) -> None:
        transcript_text = (
            "SERIES: Security Now!\n"
            "EPISODE: 1074\n"
            "TITLE: What Mythos Means\n\n"
            "Leo Laporte: Hello"
        )
        first_client = FakeClient(
            {
                MAIN_URL: _result(
                    MAIN_URL, '<a href="sn/sn-1074.txt">SN 1074 transcript</a>'
                ),
                TXT_URL: _result(TXT_URL, transcript_text),
            }
        )
        second_client = FakeClient(
            {
                MAIN_URL: _result(
                    MAIN_URL, '<a href="sn/sn-1074.txt">SN 1074 transcript</a>'
                ),
                TXT_URL: AssertionError("full transcript download should be skipped"),
            },
            metadata_responses={
                TXT_URL: _metadata(
                    TXT_URL, content_length=len(transcript_text.encode("utf-8"))
                )
            },
        )
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            first_exit_code, first_archive_state = sync_archive(
                root, client=first_client
            )
            self.assertEqual(first_exit_code, 0)
            self.assertIn("source_sha", first_archive_state["episodes"]["1074"])

            second_exit_code, second_archive_state = sync_archive(
                root, client=second_client, force=True
            )

            self.assertEqual(second_exit_code, 0)
            self.assertEqual(
                second_archive_state["episodes"]["1074"]["status"], "present"
            )
            self.assertNotIn(TXT_URL, second_client.calls)
            self.assertEqual(second_client.metadata_calls, [TXT_URL])

            transcript_path = root / "sn-1074-what-mythos-means.md"
            transcript_payload = transcript_path.read_text(encoding="utf-8")
            self.assertIn("source_sha:", transcript_payload)
            self.assertFalse((root / ".grc-sync").exists())
            self.assertEqual(
                second_archive_state["episodes"]["1074"]["source_sha"],
                first_archive_state["episodes"]["1074"]["source_sha"],
            )
