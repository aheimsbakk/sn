from __future__ import annotations

import re
from pathlib import Path
from typing import Any, cast

import yaml

from .normalize import slugify


EPISODE_FILE_RE = re.compile(r"^sn-(\d{4})-[a-z0-9-]+\.md$")


def load_archive_state(archive_root: Path) -> dict[str, Any]:
    episodes: dict[str, Any] = {}
    if not archive_root.exists():
        return {"episodes": episodes}
    for path in sorted(archive_root.glob("sn-*.md")):
        entry = load_episode_state(path, archive_root)
        if entry is None:
            continue
        episodes[str(entry["episode"])] = entry
    return {"episodes": episodes}


def load_episode_state(path: Path, archive_root: Path) -> dict[str, Any] | None:
    if not path.is_file() or not EPISODE_FILE_RE.match(path.name):
        return None
    metadata = _read_front_matter(path)
    episode = metadata.get("episode")
    if not isinstance(episode, int):
        return None
    title = metadata.get("title")
    title_slug = slugify(title) if isinstance(title, str) and title else None
    return {
        "episode": episode,
        "title_slug": title_slug,
        "transcript_url": _string_or_none(metadata.get("transcript_url")),
        "source_format": _string_or_none(metadata.get("source_format")),
        "original_encoding": _string_or_none(metadata.get("original_encoding")),
        "local_path": str(path.relative_to(archive_root)),
        "source_sha": _string_or_none(metadata.get("source_sha")),
        "status": "present",
    }


def _read_front_matter(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    closing_index = text.find("\n---\n", 4)
    if closing_index < 0:
        return {}
    payload = text[4:closing_index]
    loaded = yaml.safe_load(payload)
    if not isinstance(loaded, dict):
        return {}
    return cast(dict[str, Any], loaded)


def _string_or_none(value: Any) -> str | None:
    return value if isinstance(value, str) and value else None
