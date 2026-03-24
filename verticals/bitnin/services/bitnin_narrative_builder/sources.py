from __future__ import annotations

import json
import time
import sys
import urllib.request
import urllib.parse
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


GDELT_DOC_API_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
GDELT_MIN_INTERVAL_SECONDS = 5.0

from pathlib import Path
BITNIN_ROOT = Path(__file__).resolve().parents[2] # verticals/bitnin/


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def parse_iso_to_gdelt(value: str) -> str:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
    return dt.strftime("%Y%m%d%H%M%S")


def sanitize_query(query: str) -> str:
    compact = " ".join(query.strip().split())
    if " OR " in compact.upper() and not compact.startswith("("):
        return f"({compact})"
    return compact


@dataclass(frozen=True)
class RawNarrativeFetchResult:
    source: str
    query: str
    requested_at: str
    endpoint: str
    params: dict[str, Any]
    payload: dict[str, Any]


class GDELTDocSource:
    _last_request_at: float = 0.0
    _sync_file = BITNIN_ROOT / "runtime" / ".gdelt_last_request"

    def __init__(self, timeout: int = 30, retries: int = 5):
        self.timeout = timeout
        self.retries = retries
        self._sync_file.parent.mkdir(parents=True, exist_ok=True)

    def fetch_articles(
        self,
        *,
        query: str,
        maxrecords: int = 50,
        timespan: str = "1d",
        start: str | None = None,
        end: str | None = None,
        sort: str = "datedesc",
    ) -> RawNarrativeFetchResult:
        sanitized_query = sanitize_query(query)
        params: dict[str, Any] = {
            "query": sanitized_query,
            "mode": "artlist",
            "format": "json",
            "maxrecords": min(maxrecords, 250),
            "sort": sort,
        }
        if start or end:
            if start:
                params["startdatetime"] = parse_iso_to_gdelt(start)
            if end:
                params["enddatetime"] = parse_iso_to_gdelt(end)
        else:
            params["timespan"] = timespan

        last_error = None
        import random
        for attempt in range(self.retries):
            self._respect_rate_limit()
            query_string = urllib.parse.urlencode(params)
            url = f"{GDELT_DOC_API_URL}?{query_string}"
            
            try:
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req, timeout=self.timeout) as response:
                    self._update_last_request()
                    payload = self._parse_payload(response)
            except urllib.error.HTTPError as e:
                self._update_last_request()
                if e.code == 429:
                    error_msg = e.read().decode('utf-8').strip()
                    last_error = RuntimeError(f"GDELT 429: {error_msg}")
                    # Exponential backoff: 5, 10, 20, 40, 80... with jitter
                    delay = (GDELT_MIN_INTERVAL_SECONDS * (2 ** attempt)) + (random.random() * 2)
                    print(f"DEBUG: GDELT Rate Limit hit. Retrying in {delay:.2f}s (Attempt {attempt+1}/{self.retries})", file=sys.stderr)
                    time.sleep(delay)
                    continue
                raise
            except (urllib.error.URLError, TimeoutError) as e:
                last_error = RuntimeError(f"Network error: {e}")
                delay = (GDELT_MIN_INTERVAL_SECONDS * (attempt + 1)) + (random.random() * 2)
                print(f"DEBUG: GDELT Network issue. Retrying in {delay:.2f}s (Attempt {attempt+1}/{self.retries})", file=sys.stderr)
                time.sleep(delay)
                continue

            if "articles" not in payload:
                raise RuntimeError(f"Unexpected GDELT payload: {json.dumps(payload)[:400]}")

            return RawNarrativeFetchResult(
                source="gdelt_doc_artlist",
                query=sanitized_query,
                requested_at=utc_now_iso(),
                endpoint=GDELT_DOC_API_URL,
                params=params,
                payload=payload,
            )

        raise RuntimeError(f"GDELT persistent failure after {self.retries} attempts. Last error: {last_error}")

    def _respect_rate_limit(self) -> None:
        """Process-safe rate limiting using a shared timestamp file."""
        now = time.time()
        last_req = 0.0
        
        if self._sync_file.exists():
            try:
                last_req = float(self._sync_file.read_text().strip())
            except (ValueError, OSError):
                pass
        
        # Also check class attribute for same-process threads if any
        last_req = max(last_req, self.__class__._last_request_at)
        
        elapsed = now - last_req
        wait_seconds = GDELT_MIN_INTERVAL_SECONDS - elapsed
        if wait_seconds > 0:
            time.sleep(wait_seconds)

    def _update_last_request(self) -> None:
        """Update both memory and file-based timestamps."""
        now = time.time()
        self.__class__._last_request_at = now
        try:
            self._sync_file.write_text(str(now))
        except OSError:
            pass

    def _parse_payload(self, response: Any) -> dict[str, Any]:
        content_type = response.headers.get("Content-Type", "")
        text = response.read().decode("utf-8").strip()
        if "json" in content_type.lower() or text.startswith("{"):
            return json.loads(text)
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"GDELT non-JSON response: {text[:300]}") from exc
