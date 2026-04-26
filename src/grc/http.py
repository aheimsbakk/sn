from __future__ import annotations

import time
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .models import FetchResult


USER_AGENT = "grc/0.2.0 (+https://www.grc.com/)"


@dataclass(slots=True)
class HttpClient:
    pause_seconds: float = 2.0
    timeout_seconds: float = 20.0
    max_retries: int = 2
    backoff_seconds: float = 5.0
    _last_request_at: float | None = None

    def fetch(self, url: str) -> FetchResult:
        attempts = self.max_retries + 1
        last_error: Exception | None = None
        for attempt in range(attempts):
            self._sleep_if_needed()
            try:
                request = Request(url, headers={"User-Agent": USER_AGENT})
                with urlopen(request, timeout=self.timeout_seconds) as response:
                    payload = response.read()
                    content_type = response.headers.get_content_type()
                    charset = response.headers.get_content_charset()
                    self._last_request_at = time.monotonic()
                    return FetchResult(
                        url=url,
                        status_code=getattr(response, "status", 200),
                        data=payload,
                        content_type=content_type,
                        charset=charset,
                    )
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
