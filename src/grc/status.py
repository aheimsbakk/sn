from __future__ import annotations

import json
from typing import Any


NON_PRESENT_STATUSES = ("remote_missing", "fetch_error", "parse_error")


def summarize_archive_state(archive_state: dict[str, Any]) -> dict[str, int]:
    episodes = archive_state.get("episodes", {})
    if not isinstance(episodes, dict):
        episodes = {}
    summary = {
        "total_episodes_discovered": len(episodes),
        "total_episodes_stored_locally": 0,
        "present": 0,
        "remote_missing": 0,
        "fetch_error": 0,
        "parse_error": 0,
    }
    for item in episodes.values():
        if not isinstance(item, dict):
            continue
        status = item.get("status")
        if status in summary:
            summary[status] += 1
        if status == "present" and item.get("local_path"):
            summary["total_episodes_stored_locally"] += 1
    return summary


def list_non_present(archive_state: dict[str, Any]) -> list[dict[str, Any]]:
    episodes = archive_state.get("episodes", {})
    if not isinstance(episodes, dict):
        episodes = {}
    results = [
        item
        for item in episodes.values()
        if isinstance(item, dict) and item.get("status") in NON_PRESENT_STATUSES
    ]
    return sorted(results, key=lambda item: int(item["episode"]))


def render_status_text(
    summary: dict[str, int], missing: list[dict[str, Any]] | None = None
) -> str:
    lines = [
        f"discovered: {summary['total_episodes_discovered']}",
        f"stored: {summary['total_episodes_stored_locally']}",
        f"present: {summary['present']}",
        f"remote_missing: {summary['remote_missing']}",
        f"fetch_error: {summary['fetch_error']}",
        f"parse_error: {summary['parse_error']}",
    ]
    for item in missing or []:
        lines.append(
            f"episode {item['episode']}: {item['status']} - {item.get('last_error_summary') or 'no details'}"
        )
    return "\n".join(lines)


def render_status_json(
    summary: dict[str, int], missing: list[dict[str, Any]] | None = None
) -> str:
    payload: dict[str, Any] = dict(summary)
    if missing is not None:
        payload["episodes"] = missing
    return json.dumps(payload, indent=2, sort_keys=True)
