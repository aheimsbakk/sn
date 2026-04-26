from __future__ import annotations

import re
from importlib import import_module
from urllib.parse import urljoin

from .models import EpisodeIndexEntry
from .normalize import normalize_text


def discover_yearly_archive_urls(base_url: str, document_text: str) -> list[str]:
    html = import_module("lxml.html")
    root = html.fromstring(document_text)
    urls: list[str] = []
    for href in root.xpath("//a/@href"):
        absolute = urljoin(base_url, href)
        if _is_yearly_archive_url(absolute) and absolute not in urls:
            urls.append(absolute)
    return urls


def parse_archive_entries(base_url: str, document_text: str) -> list[EpisodeIndexEntry]:
    html = import_module("lxml.html")
    root = html.fromstring(document_text)
    entries: dict[int, EpisodeIndexEntry] = {}

    for anchor in root.xpath("//a[@href]"):
        href = anchor.get("href") or ""
        absolute = urljoin(base_url, href)
        text = normalize_text("".join(anchor.itertext()))
        episode = _extract_episode(absolute, text)
        if episode is None:
            continue
        entry = entries.get(episode)
        if entry is None:
            entry = EpisodeIndexEntry(
                episode=episode,
                title=text or f"Episode {episode}",
                archive_url=base_url,
                year=_extract_year(base_url),
            )
            entries[episode] = entry
        if absolute.endswith(".txt"):
            entry.transcript_txt_url = absolute
        elif absolute.endswith(".htm") or absolute.endswith(".html"):
            entry.transcript_html_url = absolute
        if text and len(text) > len(entry.title):
            entry.title = text

    return sorted(entries.values(), key=lambda item: item.episode)


def _extract_episode(url: str, text: str) -> int | None:
    for candidate in (url, text):
        match = re.search(r"sn[- ]?(\d{1,4})", candidate, flags=re.IGNORECASE)
        if match:
            return int(match.group(1))
        match = re.search(r"episode\s+(\d{1,4})", candidate, flags=re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None


def _is_yearly_archive_url(url: str) -> bool:
    return bool(
        re.search(r"/sn/past/(20\d{2}|2005|2006|2007|2008|2009|201\d)\.htm$", url)
    )


def _extract_year(url: str) -> int | None:
    match = re.search(r"/sn/past/(\d{4})\.htm$", url)
    if match:
        return int(match.group(1))
    return None
