from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import requests


GDELT_DOC_API_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
GDELT_MIN_INTERVAL_SECONDS = 5.0


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

    def __init__(self, session: requests.Session | None = None, timeout: int = 30, retries: int = 3):
        self.session = session or requests.Session()
        self.timeout = timeout
        self.retries = retries

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
        for attempt in range(self.retries):
            self._respect_rate_limit()
            response = self.session.get(GDELT_DOC_API_URL, params=params, timeout=self.timeout)
            self.__class__._last_request_at = time.monotonic()

            if response.status_code == 429:
                last_error = RuntimeError(response.text.strip())
                time.sleep(GDELT_MIN_INTERVAL_SECONDS * (attempt + 1))
                continue

            response.raise_for_status()
            payload = self._parse_json_payload(response)
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

        raise RuntimeError(f"GDELT rate limit or fetch error: {last_error}")

    def _respect_rate_limit(self) -> None:
        elapsed = time.monotonic() - self.__class__._last_request_at
        wait_seconds = GDELT_MIN_INTERVAL_SECONDS - elapsed
        if wait_seconds > 0:
            time.sleep(wait_seconds)

    def _parse_json_payload(self, response: requests.Response) -> dict[str, Any]:
        content_type = response.headers.get("Content-Type", "")
        if "json" in content_type.lower():
            return response.json()

        text = response.text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"GDELT non-JSON response: {text[:300]}") from exc
