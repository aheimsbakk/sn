from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol, TextIO, cast

from .archive_state import load_archive_state
from .archive_index import discover_yearly_archive_urls, parse_archive_entries
from .html_parser import parse_html_transcript
from .http import FetchError, HttpClient, RemoteMissingError
from .markdown_writer import target_markdown_path, write_markdown
from .models import (
    EpisodeIndexEntry,
    FetchResult,
    RemoteMetadata,
    SyncPlan,
    TranscriptRecord,
)
from .normalize import detect_and_decode, slugify
from .text_parser import parse_text_transcript


MAIN_ARCHIVE_URL = "https://www.grc.com/securitynow.htm"


class SupportsFetch(Protocol):
    def fetch(self, url: str) -> FetchResult: ...

    def fetch_metadata(self, url: str) -> RemoteMetadata: ...


def plan_sync(
    entries: list[EpisodeIndexEntry],
    archive_state: dict[str, Any],
    archive_root: Path,
    *,
    force: bool,
    year: int | None,
    latest: int | None,
) -> SyncPlan:
    filtered = [entry for entry in entries if _matches_year(entry, year)]
    if latest is not None:
        filtered = sorted(filtered, key=lambda item: item.episode)[-latest:]
    existing_episodes = archive_state.get("episodes", {})
    if not isinstance(existing_episodes, dict):
        existing_episodes = {}
    to_fetch: list[EpisodeIndexEntry] = []
    skipped_existing: list[int] = []
    for entry in filtered:
        existing = existing_episodes.get(str(entry.episode), {})
        if not isinstance(existing, dict):
            existing = {}
        local_path = _existing_local_path(archive_root, entry, existing)
        if not force and existing.get("status") == "present" and local_path.exists():
            skipped_existing.append(entry.episode)
            continue
        to_fetch.append(entry)
    return SyncPlan(to_fetch=to_fetch, skipped_existing=skipped_existing)


def sync_archive(
    archive_root: Path,
    *,
    client: SupportsFetch,
    year: int | None = None,
    latest: int | None = None,
    force: bool = False,
    dry_run: bool = False,
    source_preference: str = "auto",
    verbose: int = 0,
    output: TextIO | None = None,
) -> tuple[int, dict[str, Any]]:
    archive_state = load_archive_state(archive_root)
    entries = discover_episode_entries(
        client, year=year, verbose=verbose, output=output
    )
    plan = plan_sync(
        entries,
        archive_state,
        archive_root,
        force=force,
        year=year,
        latest=latest,
    )
    partial = False

    for entry in plan.to_fetch:
        existing_episodes = archive_state.get("episodes", {})
        existing = existing_episodes.get(str(entry.episode), {})
        if not isinstance(existing, dict):
            existing = {}
        if dry_run:
            _emit(
                output,
                verbose,
                f"plan transcript {entry.episode}: {_choose_url(entry, source_preference) or 'no transcript url'}",
            )
            continue
        if force and _skip_download_for_unchanged_metadata(
            client,
            archive_root,
            entry,
            existing,
            source_preference,
            verbose=verbose,
            output=output,
        ):
            continue
        try:
            record, _ = fetch_and_parse_entry(
                client,
                entry,
                source_preference,
                verbose=verbose,
                output=output,
            )
            output_path = write_markdown(archive_root, record)
            archive_state["episodes"][str(record.episode)] = _present_episode_state(
                record, output_path, archive_root
            )
            _emit(
                output,
                verbose,
                f"stored transcript {record.episode}: {output_path.relative_to(archive_root)}",
            )
        except RemoteMissingError as error:
            partial = True
            archive_state["episodes"][str(entry.episode)] = _error_episode_state(
                entry, source_preference, "remote_missing", str(error)
            )
            _emit(output, verbose, f"missing transcript {entry.episode}: {error}")
        except FetchError as error:
            partial = True
            archive_state["episodes"][str(entry.episode)] = _error_episode_state(
                entry, source_preference, "fetch_error", str(error)
            )
            _emit(output, verbose, f"fetch error {entry.episode}: {error}")
        except ValueError as error:
            partial = True
            archive_state["episodes"][str(entry.episode)] = _error_episode_state(
                entry, source_preference, "parse_error", str(error)
            )
            _emit(output, verbose, f"parse error {entry.episode}: {error}")
    return (2 if partial else 0), archive_state


def discover_episode_entries(
    client: SupportsFetch,
    *,
    year: int | None = None,
    verbose: int = 0,
    output: TextIO | None = None,
) -> list[EpisodeIndexEntry]:
    _emit(output, verbose, f"fetch archive index: {MAIN_ARCHIVE_URL}")
    main_page = client.fetch(MAIN_ARCHIVE_URL)
    main_text, _ = detect_and_decode(main_page.data, main_page.charset)
    yearly_urls = discover_yearly_archive_urls(MAIN_ARCHIVE_URL, main_text)
    urls = _select_archive_urls(year, yearly_urls)

    entries: dict[int, EpisodeIndexEntry] = {}
    for url in urls:
        if url == MAIN_ARCHIVE_URL:
            text = main_text
        else:
            _emit(output, verbose, f"fetch archive index: {url}")
            result = client.fetch(url)
            text, _ = detect_and_decode(result.data, result.charset)
        for entry in parse_archive_entries(url, text):
            existing = entries.get(entry.episode)
            if existing is None:
                entries[entry.episode] = entry
                continue
            existing.title = entry.title or existing.title
            existing.year = existing.year or entry.year
            existing.transcript_txt_url = (
                existing.transcript_txt_url or entry.transcript_txt_url
            )
            existing.transcript_html_url = (
                existing.transcript_html_url or entry.transcript_html_url
            )
    return sorted(entries.values(), key=lambda item: item.episode)


def fetch_and_parse_entry(
    client: SupportsFetch,
    entry: EpisodeIndexEntry,
    source_preference: str,
    *,
    verbose: int = 0,
    output: TextIO | None = None,
) -> tuple[TranscriptRecord, str | None]:
    urls = _candidate_urls(entry, source_preference)
    last_error: Exception | None = None
    for source_format, url in urls:
        try:
            _emit(output, verbose, f"fetch transcript {source_format}: {url}")
            result = client.fetch(url)
            text, encoding = detect_and_decode(result.data, result.charset)
            source_sha = build_source_sha(
                etag=result.etag,
                last_modified=result.last_modified,
                content_length=result.content_length,
            )
            if source_format == "txt":
                record = parse_text_transcript(
                    text, transcript_url=url, original_encoding=encoding
                )
            else:
                record = parse_html_transcript(
                    text, transcript_url=url, original_encoding=encoding
                )
            if record.episode == 0:
                record.episode = entry.episode
            if not record.title or record.title == f"Episode {record.episode}":
                record.title = entry.title
            if not record.description:
                record.description = entry.description
            record.source_sha = source_sha
            return cast(TranscriptRecord, record), source_sha
        except RemoteMissingError as error:
            last_error = error
            continue
        except Exception as error:  # noqa: BLE001
            last_error = error
            if (
                source_format == "txt"
                and source_preference == "auto"
                and entry.transcript_html_url
            ):
                continue
            raise ValueError(str(error)) from error
    if isinstance(last_error, RemoteMissingError):
        raise last_error
    if last_error is not None:
        raise ValueError(str(last_error)) from last_error
    raise RemoteMissingError(_choose_url(entry, source_preference) or "")


def _candidate_urls(
    entry: EpisodeIndexEntry, source_preference: str
) -> list[tuple[str, str]]:
    if source_preference == "txt":
        return [("txt", entry.transcript_txt_url)] if entry.transcript_txt_url else []
    if source_preference == "html":
        return (
            [("html", entry.transcript_html_url)] if entry.transcript_html_url else []
        )
    candidates: list[tuple[str, str]] = []
    if entry.transcript_txt_url:
        candidates.append(("txt", entry.transcript_txt_url))
    if entry.transcript_html_url:
        candidates.append(("html", entry.transcript_html_url))
    return candidates


def _choose_url(entry: EpisodeIndexEntry, source_preference: str) -> str | None:
    candidates = _candidate_urls(entry, source_preference)
    return candidates[0][1] if candidates else None


def _matches_year(entry: EpisodeIndexEntry, year: int | None) -> bool:
    if year is None:
        return True
    entry_year = entry.year or _derive_year(entry)
    return entry_year == year


def _select_archive_urls(year: int | None, yearly_urls: list[str]) -> list[str]:
    if year is None:
        return [MAIN_ARCHIVE_URL, *yearly_urls]
    year_suffix = f"/{year}.htm"
    for url in yearly_urls:
        if url.endswith(year_suffix):
            return [url]
    if year == datetime.now(UTC).year:
        return [MAIN_ARCHIVE_URL]
    return []


def _derive_year(entry: EpisodeIndexEntry) -> int | None:
    if entry.published:
        match = __import__("re").search(r"(\d{4})", entry.published)
        if match:
            return int(match.group(1))
    return None


def _placeholder_record(entry: EpisodeIndexEntry) -> TranscriptRecord:
    return TranscriptRecord(
        series="Security Now!", episode=entry.episode, title=entry.title, published=None
    )


def _emit(output: TextIO | None, verbose: int, message: str) -> None:
    if verbose <= 0 or output is None:
        return
    output.write(f"{message}\n")


def build_source_sha(
    *,
    etag: str | None,
    last_modified: str | None,
    content_length: int | None,
) -> str | None:
    parts: list[str] = []
    if etag:
        parts.append(f"etag:{etag.strip()}")
    if last_modified:
        parts.append(f"last-modified:{last_modified.strip()}")
    if content_length is not None:
        parts.append(f"content-length:{content_length}")
    if not parts:
        return None
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()


def _skip_download_for_unchanged_metadata(
    client: SupportsFetch,
    archive_root: Path,
    entry: EpisodeIndexEntry,
    existing: dict[str, Any],
    source_preference: str,
    *,
    verbose: int,
    output: TextIO | None,
) -> bool:
    if existing.get("status") != "present":
        return False
    local_path = _existing_local_path(archive_root, entry, existing)
    if not local_path.exists():
        return False
    existing_sha = existing.get("source_sha") or existing.get("source_hash")
    if not isinstance(existing_sha, str) or not existing_sha:
        return False
    remote_sha = _fetch_remote_source_sha(
        client, entry, source_preference, verbose=verbose, output=output
    )
    if remote_sha is None or remote_sha != existing_sha:
        return False
    existing["source_sha"] = existing_sha
    _emit(
        output, verbose, f"unchanged transcript {entry.episode}: metadata sha matched"
    )
    return True


def _fetch_remote_source_sha(
    client: SupportsFetch,
    entry: EpisodeIndexEntry,
    source_preference: str,
    *,
    verbose: int,
    output: TextIO | None,
) -> str | None:
    urls = _candidate_urls(entry, source_preference)
    last_error: Exception | None = None
    for source_format, url in urls:
        try:
            _emit(output, verbose, f"fetch transcript metadata {source_format}: {url}")
            metadata = client.fetch_metadata(url)
            source_sha = build_source_sha(
                etag=metadata.etag,
                last_modified=metadata.last_modified,
                content_length=metadata.content_length,
            )
            if source_sha:
                return source_sha
            last_error = ValueError(f"missing metadata checksum fields for {url}")
            if (
                source_preference == "auto"
                and source_format == "txt"
                and entry.transcript_html_url
            ):
                continue
            return None
        except RemoteMissingError as error:
            last_error = error
            if (
                source_preference == "auto"
                and source_format == "txt"
                and entry.transcript_html_url
            ):
                continue
            return None
        except FetchError:
            return None
    if isinstance(last_error, RemoteMissingError):
        return None
    return None


def _existing_local_path(
    archive_root: Path, entry: EpisodeIndexEntry, existing: dict[str, Any]
) -> Path:
    stored_local_path = existing.get("local_path")
    if isinstance(stored_local_path, str) and stored_local_path:
        return archive_root / stored_local_path
    return target_markdown_path(archive_root, _placeholder_record(entry))


def _present_episode_state(
    record: TranscriptRecord, output_path: Path, archive_root: Path
) -> dict[str, Any]:
    return {
        "episode": record.episode,
        "title_slug": slugify(record.title),
        "transcript_url": record.transcript_url,
        "source_format": record.source_format,
        "original_encoding": record.original_encoding,
        "local_path": str(output_path.relative_to(archive_root)),
        "source_sha": record.source_sha,
        "status": "present",
    }


def _error_episode_state(
    entry: EpisodeIndexEntry,
    source_preference: str,
    status: str,
    error: str,
) -> dict[str, Any]:
    return {
        "episode": entry.episode,
        "title_slug": slugify(entry.title),
        "transcript_url": _choose_url(entry, source_preference),
        "source_format": None,
        "original_encoding": None,
        "local_path": None,
        "source_sha": None,
        "status": status,
        "last_error_summary": error,
    }
