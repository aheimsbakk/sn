from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .models import FetchResult, RemoteMetadata


USER_AGENT = "sn/2.0.0 (+https://www.grc.com/)"


@dataclass(slots=True)
class HttpClient:
    pause_seconds: float = 2.0
    timeout_seconds: float = 20.0
    max_retries: int = 2
    backoff_seconds: float = 5.0
    _last_request_at: float | None = None

    def fetch(self, url: str) -> FetchResult:
        return self._request_fetch_result(url, method="GET")

    def fetch_metadata(self, url: str) -> RemoteMetadata:
        return self._request_remote_metadata(url, method="HEAD")

    def _request_fetch_result(self, url: str, *, method: str) -> FetchResult:
        response_data = self._request(url, method=method)
        return FetchResult(**response_data)

    def _request_remote_metadata(self, url: str, *, method: str) -> RemoteMetadata:
        response_data = self._request(url, method=method)
        response_data.pop("data", None)
        return RemoteMetadata(**response_data)

    def _request(self, url: str, *, method: str) -> dict[str, Any]:
        attempts = self.max_retries + 1
        last_error: Exception | None = None
        for attempt in range(attempts):
            self._sleep_if_needed()
            try:
                request = Request(
                    url, headers={"User-Agent": USER_AGENT}, method=method
                )
                with urlopen(request, timeout=self.timeout_seconds) as response:
                    content_type = response.headers.get_content_type()
                    charset = response.headers.get_content_charset()
                    etag = response.headers.get("ETag")
                    last_modified = response.headers.get("Last-Modified")
                    content_length_header = response.headers.get("Content-Length")
                    content_length = (
                        int(content_length_header)
                        if content_length_header and content_length_header.isdigit()
                        else None
                    )
                    self._last_request_at = time.monotonic()
                    payload = b""
                    if method != "HEAD":
                        payload = response.read()
                    return {
                        "url": url,
                        "status_code": getattr(response, "status", 200),
                        "data": payload,
                        "content_type": content_type,
                        "charset": charset,
                        "etag": etag,
                        "last_modified": last_modified,
                        "content_length": content_length,
                    }
            except HTTPError as error:
                self._last_request_at = time.monotonic()
                if error.code == 404:
                    raise RemoteMissingError(
                        url, f"missing transcript: {url}"
                    ) from error
                last_error = error
            except URLError as error:
                last_error = error

            if attempt < attempts - 1:
                time.sleep(self.backoff_seconds * (attempt + 1))

        raise FetchError(url, str(last_error) if last_error else "unknown fetch error")

    def _sleep_if_needed(self) -> None:
        if self._last_request_at is None:
            return
        elapsed = time.monotonic() - self._last_request_at
        delay = self.pause_seconds - elapsed
        if delay > 0:
            time.sleep(delay)


class FetchError(RuntimeError):
    def __init__(self, url: str, message: str | None = None) -> None:
        super().__init__(message or url)
        self.url = url


class RemoteMissingError(FetchError):
    pass


def is_supported_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
