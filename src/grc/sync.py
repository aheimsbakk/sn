from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Protocol, TextIO, cast

from .archive_index import discover_yearly_archive_urls, parse_archive_entries
from .html_parser import parse_html_transcript
from .http import FetchError, HttpClient, RemoteMissingError
from .manifest import load_manifest, save_manifest, update_episode_manifest
from .markdown_writer import target_markdown_path, write_markdown
from .models import EpisodeIndexEntry, FetchResult, SyncPlan, TranscriptRecord
from .normalize import detect_and_decode, slugify
from .text_parser import parse_text_transcript


MAIN_ARCHIVE_URL = "https://www.grc.com/securitynow.htm"


class SupportsFetch(Protocol):
    def fetch(self, url: str) -> FetchResult: ...


def plan_sync(
    entries: list[EpisodeIndexEntry],
    manifest: dict[str, Any],
    archive_root: Path,
    *,
    force: bool,
    from_episode: int | None,
    to_episode: int | None,
    latest: int | None,
) -> SyncPlan:
    filtered = [
        entry for entry in entries if _in_range(entry.episode, from_episode, to_episode)
    ]
    if latest is not None:
        filtered = sorted(filtered, key=lambda item: item.episode)[-latest:]
    manifest_episodes = manifest.get("episodes", {})
    if not isinstance(manifest_episodes, dict):
        manifest_episodes = {}
    to_fetch: list[EpisodeIndexEntry] = []
    skipped_existing: list[int] = []
    for entry in filtered:
        existing = manifest_episodes.get(str(entry.episode), {})
        if not isinstance(existing, dict):
            existing = {}
        local_path = target_markdown_path(archive_root, _placeholder_record(entry))
        if not force and existing.get("status") == "present" and local_path.exists():
            skipped_existing.append(entry.episode)
            continue
        to_fetch.append(entry)
    return SyncPlan(to_fetch=to_fetch, skipped_existing=skipped_existing)


def sync_archive(
    archive_root: Path,
    *,
    client: SupportsFetch,
    from_episode: int | None = None,
    to_episode: int | None = None,
    latest: int | None = None,
    force: bool = False,
    dry_run: bool = False,
    source_preference: str = "auto",
    verbose: int = 0,
    output: TextIO | None = None,
) -> tuple[int, dict[str, Any]]:
    manifest = load_manifest(archive_root)
    entries = discover_episode_entries(client, verbose=verbose, output=output)
    plan = plan_sync(
        entries,
        manifest,
        archive_root,
        force=force,
        from_episode=from_episode,
        to_episode=to_episode,
        latest=latest,
    )
    partial = False

    try:
        for entry in plan.to_fetch:
            if dry_run:
                _emit(
                    output,
                    verbose,
                    f"plan transcript {entry.episode}: {_choose_url(entry, source_preference) or 'no transcript url'}",
                )
                update_episode_manifest(
                    manifest,
                    episode=entry.episode,
                    title_slug=slugify(entry.title),
                    transcript_url=_choose_url(entry, source_preference),
                    source_format=None,
                    original_encoding=None,
                    local_path=None,
                    source_hash=None,
                    status="fetch_error",
                    error="dry-run",
                )
                continue
            try:
                record, source_hash = fetch_and_parse_entry(
                    client,
                    entry,
                    source_preference,
                    verbose=verbose,
                    output=output,
                )
                output_path = write_markdown(archive_root, record)
                update_episode_manifest(
                    manifest,
                    episode=record.episode,
                    title_slug=slugify(record.title),
                    transcript_url=record.transcript_url,
                    source_format=record.source_format,
                    original_encoding=record.original_encoding,
                    local_path=str(output_path.relative_to(archive_root)),
                    source_hash=source_hash,
                    status="present",
                )
                _emit(
                    output,
                    verbose,
                    f"stored transcript {record.episode}: {output_path.relative_to(archive_root)}",
                )
            except RemoteMissingError as error:
                partial = True
                update_episode_manifest(
                    manifest,
                    episode=entry.episode,
                    title_slug=slugify(entry.title),
                    transcript_url=_choose_url(entry, source_preference),
                    source_format=None,
                    original_encoding=None,
                    local_path=None,
                    source_hash=None,
                    status="remote_missing",
                    error=str(error),
                )
                _emit(output, verbose, f"missing transcript {entry.episode}: {error}")
            except FetchError as error:
                partial = True
                update_episode_manifest(
                    manifest,
                    episode=entry.episode,
                    title_slug=slugify(entry.title),
                    transcript_url=_choose_url(entry, source_preference),
                    source_format=None,
                    original_encoding=None,
                    local_path=None,
                    source_hash=None,
                    status="fetch_error",
                    error=str(error),
                )
                _emit(output, verbose, f"fetch error {entry.episode}: {error}")
            except ValueError as error:
                partial = True
                update_episode_manifest(
                    manifest,
                    episode=entry.episode,
                    title_slug=slugify(entry.title),
                    transcript_url=_choose_url(entry, source_preference),
                    source_format=None,
                    original_encoding=None,
                    local_path=None,
                    source_hash=None,
                    status="parse_error",
                    error=str(error),
                )
                _emit(output, verbose, f"parse error {entry.episode}: {error}")
    finally:
        save_manifest(archive_root, manifest)
    return (2 if partial else 0), manifest


def discover_episode_entries(
    client: SupportsFetch, *, verbose: int = 0, output: TextIO | None = None
) -> list[EpisodeIndexEntry]:
    _emit(output, verbose, f"fetch archive index: {MAIN_ARCHIVE_URL}")
    main_page = client.fetch(MAIN_ARCHIVE_URL)
    main_text, _ = detect_and_decode(main_page.data, main_page.charset)
    urls = [
        MAIN_ARCHIVE_URL,
        *discover_yearly_archive_urls(MAIN_ARCHIVE_URL, main_text),
    ]

    entries: dict[int, EpisodeIndexEntry] = {}
    for url in urls:
        if url != MAIN_ARCHIVE_URL:
            _emit(output, verbose, f"fetch archive index: {url}")
        result = client.fetch(url)
        text, _ = detect_and_decode(result.data, result.charset)
        for entry in parse_archive_entries(url, text):
            existing = entries.get(entry.episode)
            if existing is None:
                entries[entry.episode] = entry
                continue
            existing.title = entry.title or existing.title
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
) -> tuple[TranscriptRecord, str]:
    urls = _candidate_urls(entry, source_preference)
    last_error: Exception | None = None
    for source_format, url in urls:
        try:
            _emit(output, verbose, f"fetch transcript {source_format}: {url}")
            result = client.fetch(url)
            text, encoding = detect_and_decode(result.data, result.charset)
            source_hash = hashlib.sha256(result.data).hexdigest()
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
            return cast(TranscriptRecord, record), source_hash
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


def _in_range(episode: int, from_episode: int | None, to_episode: int | None) -> bool:
    if from_episode is not None and episode < from_episode:
        return False
    if to_episode is not None and episode > to_episode:
        return False
    return True


def _placeholder_record(entry: EpisodeIndexEntry) -> TranscriptRecord:
    return TranscriptRecord(
        series="Security Now!", episode=entry.episode, title=entry.title, published=None
    )


def _emit(output: TextIO | None, verbose: int, message: str) -> None:
    if verbose <= 0 or output is None:
        return
    output.write(f"{message}\n")
