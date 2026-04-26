from __future__ import annotations

from collections import OrderedDict
from pathlib import Path

import yaml

from .models import TranscriptRecord
from .normalize import slugify


def build_markdown(record: TranscriptRecord) -> str:
    metadata = OrderedDict()
    metadata["series"] = record.series
    metadata["episode"] = record.episode
    metadata["title"] = record.title
    metadata["published"] = record.published
    metadata["speakers"] = record.speakers
    metadata["description"] = record.description
    metadata["audio_url"] = record.audio_url
    metadata["transcript_url"] = record.transcript_url
    metadata["source_format"] = record.source_format
    metadata["original_encoding"] = record.original_encoding
    metadata["license"] = record.license

    front_matter = yaml.safe_dump(
        dict(metadata), allow_unicode=True, sort_keys=False
    ).strip()

    sections = [
        f"# {record.series} Episode {record.episode}: {record.title}",
    ]
    if record.description:
        sections.extend(["", "## Description", "", record.description])
    if record.show_tease:
        sections.extend(["", "## Show tease", "", record.show_tease])
    sections.extend(["", "## Transcript", ""])
    sections.extend(record.transcript_lines or ["Transcript unavailable."])

    body = "\n".join(sections).strip() + "\n"
    return f"---\n{front_matter}\n---\n\n{body}"


def target_markdown_path(archive_root: Path, record: TranscriptRecord) -> Path:
    slug = slugify(record.title)
    return archive_root / "transcripts" / f"sn-{record.episode:04d}-{slug}.md"


def write_markdown(archive_root: Path, record: TranscriptRecord) -> Path:
    path = target_markdown_path(archive_root, record)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build_markdown(record), encoding="utf-8", newline="\n")
    return path
