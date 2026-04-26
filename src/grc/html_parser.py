from __future__ import annotations

from importlib import import_module

from .models import TranscriptRecord
from .normalize import normalize_speaker_line, normalize_text


def parse_html_transcript(
    document_text: str,
    transcript_url: str | None = None,
    original_encoding: str | None = None,
) -> TranscriptRecord:
    html = import_module("lxml.html")
    root = html.fromstring(document_text)
    title = _first_text(root.xpath("//title/text()")) or "Security Now!"
    heading = _first_text(
        root.xpath("//h1/text() | //h2/text() | //font[@size='4']/text()")
    )
    title_text = heading or title

    episode = (
        _extract_episode_number(title_text)
        or _extract_episode_number(title)
        or _extract_episode_number(transcript_url or "")
    )
    description = _extract_description(document_text) or _first_text(
        root.xpath("//meta[@name='description']/@content")
    )
    show_tease = _extract_show_tease(document_text)
    audio_url = _extract_audio_url(document_text)

    transcript_lines = []
    for font_node in root.xpath("//font[b]"):
        label = _first_text(font_node.xpath("./b[1]/text()"))
        if not label or not label.endswith(":"):
            continue
        if label.lower() == "description:":
            continue
        text_content = normalize_text(" ".join(font_node.itertext()))
        if not text_content.startswith(label):
            continue
        content = text_content[len(label) :].strip()
        if not content:
            continue
        transcript_lines.append(f"**{label[:-1]}:** {content}")

    if not transcript_lines:
        for paragraph in root.xpath("//p"):
            text_content = normalize_text(" ".join(paragraph.itertext()))
            if not text_content:
                continue
            if text_content.lower().startswith("show tease:"):
                continue
            transcript_line = normalize_speaker_line(text_content)
            if transcript_line == text_content and ":" not in text_content:
                continue
            transcript_lines.append(transcript_line)

    return TranscriptRecord(
        series="Security Now!",
        episode=episode,
        title=_clean_title(title_text, episode),
        published=None,
        speakers=[],
        description=description,
        audio_url=audio_url,
        transcript_url=transcript_url,
        source_format="html",
        original_encoding=original_encoding,
        license=None,
        show_tease=show_tease,
        transcript_lines=transcript_lines,
    )


def _first_text(values: list[str]) -> str | None:
    for value in values:
        cleaned = normalize_text(value)
        if cleaned:
            return cleaned
    return None


def _extract_episode_number(title: str) -> int:
    import re

    match = re.search(r"(?:episode\s+)?(\d{1,4})", title, flags=re.IGNORECASE)
    return int(match.group(1)) if match else 0


def _clean_title(title: str, episode: int) -> str:
    import re

    cleaned = normalize_text(title)
    cleaned = re.sub(r"^Security Now!?\s*[-: ]*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(
        rf"^Episode\s+{episode}\s*[-: ]*", "", cleaned, flags=re.IGNORECASE
    )
    cleaned = re.sub(
        r"^Transcript of Episode\s*#?\d+\s*", "", cleaned, flags=re.IGNORECASE
    )
    cleaned = cleaned.strip(" -:")
    return cleaned or f"Episode {episode}"


def _extract_description(document_text: str) -> str | None:
    import re

    match = re.search(
        r"<b>Description:</b>\s*([^<]+)", document_text, flags=re.IGNORECASE
    )
    return normalize_text(match.group(1)) if match else None


def _extract_show_tease(document_text: str) -> str | None:
    import re

    match = re.search(
        r"SHOW TEASE:\s*(.*?)\s*<p><table",
        document_text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return normalize_text(match.group(1)) if match else None


def _extract_audio_url(document_text: str) -> str | None:
    import re

    match = re.search(
        r'High quality.*?<a href="([^"]+)"',
        document_text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return normalize_text(match.group(1)) if match else None
