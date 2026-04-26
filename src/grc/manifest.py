from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast


def manifest_path(archive_root: Path) -> Path:
    return archive_root / ".grc-sync" / "manifest.json"


def load_manifest(archive_root: Path) -> dict[str, Any]:
    path = manifest_path(archive_root)
    if not path.exists():
        return {"episodes": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def save_manifest(archive_root: Path, data: dict[str, Any]) -> None:
    path = manifest_path(archive_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def update_episode_manifest(
    manifest: dict[str, Any],
    *,
    episode: int,
    title_slug: str,
    transcript_url: str | None,
    source_format: str | None,
    original_encoding: str | None,
    local_path: str | None,
    source_hash: str | None,
    status: str,
    error: str | None = None,
) -> None:
    episodes = cast(dict[str, Any], manifest.setdefault("episodes", {}))
    now = (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
    episodes[str(episode)] = {
        "episode": episode,
        "title_slug": title_slug,
        "transcript_url": transcript_url,
        "source_format": source_format,
        "original_encoding": original_encoding,
        "local_path": local_path,
        "fetched_at": now,
        "source_hash": source_hash,
        "status": status,
        "last_retry_at": now if status != "present" else None,
        "last_error_summary": error,
    }
