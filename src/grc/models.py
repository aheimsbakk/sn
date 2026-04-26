from __future__ import annotations

from dataclasses import dataclass, field


SYNC_STATUSES = {"present", "remote_missing", "fetch_error", "parse_error"}


@dataclass(slots=True)
class EpisodeIndexEntry:
    episode: int
    title: str
    transcript_txt_url: str | None = None
    transcript_html_url: str | None = None
    archive_url: str | None = None
    published: str | None = None
    description: str | None = None


@dataclass(slots=True)
class TranscriptRecord:
    series: str
    episode: int
    title: str
    published: str | None
    speakers: list[str] = field(default_factory=list)
    description: str | None = None
    audio_url: str | None = None
    transcript_url: str | None = None
    source_format: str | None = None
    original_encoding: str | None = None
    source_sha: str | None = None
    license: str | None = None
    show_tease: str | None = None
    transcript_lines: list[str] = field(default_factory=list)


@dataclass(slots=True)
class FetchResult:
    url: str
    status_code: int
    data: bytes
    content_type: str | None = None
    charset: str | None = None
    etag: str | None = None
    last_modified: str | None = None
    content_length: int | None = None


@dataclass(slots=True)
class RemoteMetadata:
    url: str
    status_code: int
    content_type: str | None = None
    charset: str | None = None
    etag: str | None = None
    last_modified: str | None = None
    content_length: int | None = None


@dataclass(slots=True)
class SyncPlan:
    to_fetch: list[EpisodeIndexEntry]
    skipped_existing: list[int]
