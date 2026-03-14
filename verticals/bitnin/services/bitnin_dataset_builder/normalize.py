from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from .sources import RawFetchResult


INTERVAL_DELTAS = {
    "1m": timedelta(minutes=1),
    "5m": timedelta(minutes=5),
    "15m": timedelta(minutes=15),
    "30m": timedelta(minutes=30),
    "1h": timedelta(hours=1),
    "4h": timedelta(hours=4),
    "1d": timedelta(days=1),
    "1w": timedelta(weeks=1),
}


def parse_utc_datetime(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def to_utc_string(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def epoch_seconds_to_utc_string(value: int | float) -> str:
    return to_utc_string(datetime.fromtimestamp(value, tz=UTC))


def epoch_millis_to_utc_string(value: int) -> str:
    return to_utc_string(datetime.fromtimestamp(value / 1000, tz=UTC))


def interval_to_delta(interval: str) -> timedelta:
    if interval not in INTERVAL_DELTAS:
        raise ValueError(f"Unsupported interval for BitNin market builder: {interval}")
    return INTERVAL_DELTAS[interval]


def decimal_to_float(value: Any) -> float:
    return float(Decimal(str(value)))


def compute_bar_checksum(record: dict[str, Any]) -> str:
    payload = {
        key: record[key]
        for key in sorted(record)
        if key != "checksum"
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def normalize_blockchain_market_price(
    raw_result: RawFetchResult,
    *,
    dataset_version: str,
    symbol: str | None = None,
) -> list[dict[str, Any]]:
    payload = raw_result.payload
    values = payload.get("values", [])
    period = payload.get("period", "day")
    if period != "day":
        raise ValueError(f"Unexpected Blockchain.com period for market-price: {period}")

    records: list[dict[str, Any]] = []
    interval = "1d"
    delta = interval_to_delta(interval)
    resolved_symbol = symbol or raw_result.symbol

    for point in values:
        open_dt = datetime.fromtimestamp(int(point["x"]), tz=UTC)
        close_dt = open_dt + delta - timedelta(milliseconds=1)
        price = decimal_to_float(point["y"])

        record: dict[str, Any] = {
            "symbol": resolved_symbol,
            "source": raw_result.source,
            "interval": interval,
            "open_time": to_utc_string(open_dt),
            "close_time": to_utc_string(close_dt),
            "open": price,
            "high": price,
            "low": price,
            "close": price,
            "volume": 0.0,
            "ingested_at": raw_result.requested_at,
            "dataset_version": dataset_version,
        }
        record["checksum"] = compute_bar_checksum(record)
        records.append(record)

    return records


def normalize_binance_klines(
    raw_result: RawFetchResult,
    *,
    dataset_version: str,
) -> list[dict[str, Any]]:
    interval = raw_result.interval
    interval_to_delta(interval)

    records: list[dict[str, Any]] = []
    for row in raw_result.payload:
        record: dict[str, Any] = {
            "symbol": raw_result.symbol,
            "source": raw_result.source,
            "interval": interval,
            "open_time": epoch_millis_to_utc_string(int(row[0])),
            "close_time": epoch_millis_to_utc_string(int(row[6])),
            "open": decimal_to_float(row[1]),
            "high": decimal_to_float(row[2]),
            "low": decimal_to_float(row[3]),
            "close": decimal_to_float(row[4]),
            "volume": decimal_to_float(row[5]),
            "ingested_at": raw_result.requested_at,
            "quote_volume": decimal_to_float(row[7]),
            "trade_count": int(row[8]),
            "dataset_version": dataset_version,
        }
        record["checksum"] = compute_bar_checksum(record)
        records.append(record)

    return records
