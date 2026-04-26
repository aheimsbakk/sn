from __future__ import annotations

import re
from typing import Any

from .models import TranscriptRecord
from .normalize import normalize_speaker_line, normalize_text


HEADER_MAP = {
    "SERIES": "series",
    "EPISODE": "episode",
    "DATE": "published",
    "TITLE": "title",
    "HOSTS": "speakers",
    "SPEAKERS": "speakers",
    "SOURCE": "audio_url",
    "SOURCE FILE": "audio_url",
    "ARCHIVE": "series_archive_url",
    "FILE ARCHIVE": "series_archive_url",
    "DESCRIPTION": "description",
    "SHOW TEASE": "show_tease",
}


SPEAKER_SPLIT_RE = re.compile(r"\s*(?:,|&| and )\s*", flags=re.IGNORECASE)


def parse_text_transcript(
    text: str, transcript_url: str | None = None, original_encoding: str | None = None
) -> TranscriptRecord:
    normalized = normalize_text(text)
    if not normalized:
        raise ValueError("empty transcript")
    lines = normalized.split("\n")
    metadata: dict[str, Any] = {}
    body_start = 0
    header_started = False

    for index, line in enumerate(lines):
        if not line:
            continue
        match = re.match(r"^([A-Z][A-Z ]+):\s*(.*)$", line)
        if not match:
            if not header_started:
                continue
            body_start = index
            break
        label, value = match.groups()
        key = HEADER_MAP.get(label.strip())
        if not key:
            if not header_started:
                continue
            body_start = index
            break
        header_started = True
        if key == "speakers":
            metadata[key] = [
                part.strip() for part in SPEAKER_SPLIT_RE.split(value) if part.strip()
            ]
        elif key == "episode":
            metadata[key] = int(value.strip().lstrip("#"))
        else:
            metadata[key] = value.strip() or None
    else:
        body_start = len(lines)

    body_lines = []
    license_lines = []
    license_mode = False
    for line in lines[body_start:]:
        lower = line.lower()
        if lower.startswith("copyright") or "creative commons" in lower:
            license_mode = True
        if license_mode:
            license_lines.append(line)
        elif line:
            body_lines.append(normalize_speaker_line(line))
        else:
            body_lines.append("")

    series = str(metadata.get("series") or "Security Now!")
    episode_value = metadata.get("episode")
    episode = int(episode_value) if episode_value is not None else 0
    title = str(metadata.get("title") or f"Episode {episode}")
    published = metadata.get("published")
    description = metadata.get("description")
    show_tease = metadata.get("show_tease")
    speakers_value = metadata.get("speakers")
    speakers = list(speakers_value) if isinstance(speakers_value, list) else []
    audio_url = metadata.get("audio_url")
    license_text = "\n".join(line for line in license_lines if line).strip() or None

    if "episode" not in metadata and "title" not in metadata:
        raise ValueError("could not parse text transcript")

    return TranscriptRecord(
        series=series,
        episode=episode,
        title=title,
        published=str(published) if published else None,
        speakers=speakers,
        description=str(description) if description else None,
        audio_url=str(audio_url) if audio_url else None,
        transcript_url=transcript_url,
        source_format="txt",
        original_encoding=original_encoding,
        license=license_text,
        show_tease=str(show_tease) if show_tease else None,
        transcript_lines=_trim_blank_edges(body_lines),
    )


def _trim_blank_edges(lines: list[str]) -> list[str]:
    trimmed = list(lines)
    while trimmed and not trimmed[0]:
        trimmed.pop(0)
    while trimmed and not trimmed[-1]:
        trimmed.pop()
    return trimmed
