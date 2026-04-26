from __future__ import annotations

import html
import re


CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
WHITESPACE_RE = re.compile(r"[ \t]+")


def detect_and_decode(data: bytes, http_charset: str | None = None) -> tuple[str, str]:
    candidates: list[str] = []
    if http_charset:
        candidates.append(http_charset)

    if data.startswith(b"\xef\xbb\xbf"):
        candidates.append("utf-8-sig")
    elif data.startswith(b"\xff\xfe") or data.startswith(b"\xfe\xff"):
        candidates.append("utf-16")

    candidates.extend(["utf-8", "cp1252", "latin-1"])

    seen: set[str] = set()
    for encoding in candidates:
        normalized = encoding.lower()
        if normalized in seen:
            continue
        seen.add(normalized)
        try:
            return data.decode(encoding), normalized
        except UnicodeDecodeError:
            continue

    return data.decode("latin-1", errors="replace"), "latin-1"


def normalize_text(value: str) -> str:
    text = value.replace("\r\n", "\n").replace("\r", "\n")
    text = html.unescape(text)
    text = CONTROL_CHARS_RE.sub("", text)
    lines = [WHITESPACE_RE.sub(" ", line).strip() for line in text.split("\n")]
    return "\n".join(lines).strip()


def slugify(value: str, max_length: int = 32) -> str:
    text = normalize_text(value).lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    text = text[:max_length].rstrip("-")
    return text or "episode"


def normalize_speaker_line(line: str) -> str:
    stripped = line.strip()
    match = re.match(r"^([A-Za-z][A-Za-z .'-]{0,60}?):\s*(.+)$", stripped)
    if not match:
        return stripped
    speaker, text = match.groups()
    return f"**{speaker.strip()}:** {text.strip()}"
