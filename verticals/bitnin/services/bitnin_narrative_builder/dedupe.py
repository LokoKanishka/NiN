from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


TRACKING_QUERY_KEYS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "utm_id",
    "gclid",
    "fbclid",
    "mc_cid",
    "mc_eid",
}


def canonicalize_url(url: str) -> str:
    parts = urlsplit(url.strip())
    scheme = parts.scheme.lower() or "https"
    netloc = parts.netloc.lower()
    path = parts.path.rstrip("/") or "/"

    clean_query_items = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if key.lower() not in TRACKING_QUERY_KEYS
    ]
    clean_query = urlencode(clean_query_items, doseq=True)
    return urlunsplit((scheme, netloc, path, clean_query, ""))


def normalize_title(title: str) -> str:
    lowered = title.lower().strip()
    lowered = re.sub(r"\s+", " ", lowered)
    return re.sub(r"[^\w\s]", "", lowered)


def hash_normalized_title(title: str) -> str:
    normalized = normalize_title(title)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _time_bucket(timestamp: str, bucket_hours: int = 6) -> int:
    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00")).astimezone(UTC)
    return int(dt.timestamp() // (bucket_hours * 3600))


def dedupe_narrative_events(events: list[dict], bucket_hours: int = 6) -> list[dict]:
    deduped: list[dict] = []
    seen_urls: set[str] = set()
    seen_title_buckets: set[tuple[str, int]] = set()

    for event in sorted(events, key=lambda item: (item["timestamp_start"], item["event_id"])):
        canonical_url = canonicalize_url(event["url"])
        title_hash = hash_normalized_title(event["title"])
        bucket = _time_bucket(event["timestamp_start"], bucket_hours=bucket_hours)

        if canonical_url in seen_urls:
            continue
        if (title_hash, bucket) in seen_title_buckets:
            continue

        event["url"] = canonical_url
        deduped.append(event)
        seen_urls.add(canonical_url)
        seen_title_buckets.add((title_hash, bucket))

    return deduped
