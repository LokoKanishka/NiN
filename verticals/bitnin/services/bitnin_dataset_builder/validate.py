from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .normalize import interval_to_delta, parse_utc_datetime


SCHEMA_PATH = Path(__file__).resolve().parents[2] / "SCHEMAS" / "market_bar.schema.json"


def load_market_bar_schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _validate_datetime_format(value: str) -> bool:
    try:
        parse_utc_datetime(value)
        return True
    except ValueError:
        return False


def validate_record_against_schema(record: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    properties = schema.get("properties", {})
    required = schema.get("required", [])

    for field_name in required:
        if field_name not in record:
            errors.append(f"missing required field `{field_name}`")

    if schema.get("additionalProperties") is False:
        extras = sorted(set(record) - set(properties))
        if extras:
            errors.append(f"unexpected fields: {', '.join(extras)}")

    for field_name, field_schema in properties.items():
        if field_name not in record:
            continue

        value = record[field_name]
        field_type = field_schema.get("type")

        if field_type == "string":
            if not isinstance(value, str):
                errors.append(f"`{field_name}` must be string")
                continue
            if field_schema.get("minLength", 0) and len(value) < field_schema["minLength"]:
                errors.append(f"`{field_name}` shorter than minLength")
            if field_schema.get("format") == "date-time" and not _validate_datetime_format(value):
                errors.append(f"`{field_name}` is not valid RFC3339 UTC datetime")
        elif field_type == "number":
            if not _is_number(value):
                errors.append(f"`{field_name}` must be number")
                continue
            minimum = field_schema.get("minimum")
            maximum = field_schema.get("maximum")
            if minimum is not None and value < minimum:
                errors.append(f"`{field_name}` below minimum")
            if maximum is not None and value > maximum:
                errors.append(f"`{field_name}` above maximum")
        elif field_type == "integer":
            if not _is_integer(value):
                errors.append(f"`{field_name}` must be integer")
                continue
            minimum = field_schema.get("minimum")
            if minimum is not None and value < minimum:
                errors.append(f"`{field_name}` below minimum")

        enum_values = field_schema.get("enum")
        if enum_values is not None and value not in enum_values:
            errors.append(f"`{field_name}` must be one of {enum_values}")

    return errors


def validate_market_bars(records: list[dict[str, Any]], schema: dict[str, Any] | None = None) -> dict[str, Any]:
    schema = schema or load_market_bar_schema()
    schema_errors: list[dict[str, Any]] = []
    duplicates: list[dict[str, Any]] = []
    gaps: list[dict[str, Any]] = []
    price_errors: list[dict[str, Any]] = []
    timestamp_errors: list[dict[str, Any]] = []

    duplicate_counter = Counter(
        (record.get("symbol"), record.get("interval"), record.get("open_time"))
        for record in records
    )
    for key, count in duplicate_counter.items():
        if count > 1:
            duplicates.append(
                {
                    "key": {
                        "symbol": key[0],
                        "interval": key[1],
                        "open_time": key[2],
                    },
                    "count": count,
                }
            )

    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for index, record in enumerate(records):
        record_errors = validate_record_against_schema(record, schema)
        if record_errors:
            schema_errors.append({"index": index, "errors": record_errors})

        try:
            open_dt = parse_utc_datetime(record["open_time"])
            close_dt = parse_utc_datetime(record["close_time"])
            if close_dt <= open_dt:
                timestamp_errors.append(
                    {
                        "index": index,
                        "reason": "close_time must be after open_time",
                        "open_time": record.get("open_time"),
                        "close_time": record.get("close_time"),
                    }
                )
        except Exception as exc:
            timestamp_errors.append(
                {
                    "index": index,
                    "reason": f"timestamp parse error: {exc}",
                    "open_time": record.get("open_time"),
                    "close_time": record.get("close_time"),
                }
            )
            continue

        low = record.get("low")
        high = record.get("high")
        open_price = record.get("open")
        close_price = record.get("close")

        if _is_number(low) and _is_number(high) and high < low:
            price_errors.append({"index": index, "reason": "high < low"})

        if _is_number(low) and _is_number(high) and _is_number(open_price):
            if not (low <= open_price <= high):
                price_errors.append({"index": index, "reason": "open outside [low, high]"})

        if _is_number(low) and _is_number(high) and _is_number(close_price):
            if not (low <= close_price <= high):
                price_errors.append({"index": index, "reason": "close outside [low, high]"})

        group_key = (record.get("symbol", ""), record.get("source", ""), record.get("interval", ""))
        grouped[group_key].append(record)

    for (symbol, source, interval), group in grouped.items():
        try:
            delta = interval_to_delta(interval)
        except ValueError:
            continue
        ordered = sorted(group, key=lambda item: item["open_time"])
        for previous, current in zip(ordered, ordered[1:]):
            previous_open = parse_utc_datetime(previous["open_time"])
            current_open = parse_utc_datetime(current["open_time"])
            diff = current_open - previous_open
            if diff > delta:
                missing = int(diff / delta) - 1
                gaps.append(
                    {
                        "symbol": symbol,
                        "source": source,
                        "interval": interval,
                        "previous_open_time": previous["open_time"],
                        "current_open_time": current["open_time"],
                        "missing_bars_estimate": missing,
                    }
                )

    return {
        "valid": not any([schema_errors, duplicates, gaps, price_errors, timestamp_errors]),
        "record_count": len(records),
        "schema_errors": schema_errors,
        "duplicates": duplicates,
        "gaps": gaps,
        "price_errors": price_errors,
        "timestamp_errors": timestamp_errors,
        "checked_at": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
    }
