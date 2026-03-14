from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .classify import build_summary_local, classify_topics, extract_entities, score_confidence_source, score_relevance_btc
from .dedupe import canonicalize_url
from .sources import RawNarrativeFetchResult


SCHEMA_PATH = Path(__file__).resolve().parents[2] / "SCHEMAS" / "narrative_event.schema.json"
SEEN_DATE_FORMAT = "%Y%m%dT%H%M%SZ"


def load_narrative_event_schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def parse_gdelt_seen_date(value: str) -> datetime:
    return datetime.strptime(value, SEEN_DATE_FORMAT).replace(tzinfo=UTC)


def to_utc_string(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def clean_text(value: str) -> str:
    return " ".join(value.strip().split())


def build_event_id(url: str, title: str, seen_date: str) -> str:
    payload = f"{canonicalize_url(url)}|{clean_text(title).lower()}|{seen_date}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def normalize_gdelt_articles(
    raw_result: RawNarrativeFetchResult,
    *,
    dataset_version: str,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for article in raw_result.payload.get("articles", []):
        url = canonicalize_url(article.get("url", "").strip())
        if not url:
            continue

        title = clean_text(article.get("title", "") or "[untitled]")
        seen_date = article.get("seendate")
        if not seen_date:
            continue

        timestamp_start = parse_gdelt_seen_date(seen_date)
        timestamp_end = timestamp_start + timedelta(minutes=1)
        source_name = clean_text(article.get("domain", "") or "GDELT")
        region = clean_text(article.get("sourcecountry", "") or "unknown")

        text_for_classification = " ".join(
            filter(
                None,
                [
                    title,
                    source_name,
                    region,
                    raw_result.query,
                ],
            )
        )
        topics = classify_topics(text_for_classification)
        entities = extract_entities(text_for_classification)
        confidence_source = score_confidence_source(article)
        relevance_btc = score_relevance_btc(text_for_classification, topics)
        summary_local = build_summary_local(
            title=title,
            source_name=source_name,
            timestamp_start=to_utc_string(timestamp_start),
            topics=topics,
            relevance_btc=relevance_btc,
            confidence_source=confidence_source,
        )

        record = {
            "event_id": build_event_id(url, title, seen_date),
            "timestamp_start": to_utc_string(timestamp_start),
            "timestamp_end": to_utc_string(timestamp_end),
            "source_name": source_name,
            "url": url,
            "title": title,
            "summary_local": summary_local,
            "topics": topics,
            "entities": entities,
            "source_type": "news_article_candidate",
            "region": region,
            "confidence_source": confidence_source,
            "relevance_btc": relevance_btc,
            "retention_mode": "metadata_only",
            "ingested_at": raw_result.requested_at,
            "dataset_version": dataset_version,
        }
        records.append(record)

    return records


def validate_narrative_events(events: list[dict[str, Any]], schema: dict[str, Any] | None = None) -> dict[str, Any]:
    schema = schema or load_narrative_event_schema()
    validator = Draft202012Validator(schema)
    schema_errors: list[dict[str, Any]] = []
    timestamp_errors: list[dict[str, Any]] = []
    duplicate_event_ids: dict[str, int] = {}

    counter: dict[str, int] = {}
    for index, event in enumerate(events):
        counter[event["event_id"]] = counter.get(event["event_id"], 0) + 1

        event_errors = [error.message for error in validator.iter_errors(event)]
        if event_errors:
            schema_errors.append({"index": index, "errors": sorted(event_errors)})

        start = datetime.fromisoformat(event["timestamp_start"].replace("Z", "+00:00"))
        end = datetime.fromisoformat(event["timestamp_end"].replace("Z", "+00:00"))
        if end < start:
            timestamp_errors.append(
                {
                    "index": index,
                    "reason": "timestamp_end earlier than timestamp_start",
                    "timestamp_start": event["timestamp_start"],
                    "timestamp_end": event["timestamp_end"],
                }
            )

    duplicate_event_ids = {key: value for key, value in counter.items() if value > 1}
    return {
        "valid": not any([schema_errors, timestamp_errors, duplicate_event_ids]),
        "record_count": len(events),
        "schema_errors": schema_errors,
        "timestamp_errors": timestamp_errors,
        "duplicate_event_ids": duplicate_event_ids,
        "checked_at": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
    }
