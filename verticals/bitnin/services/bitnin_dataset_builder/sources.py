from __future__ import annotations

import json
import urllib.request
import urllib.parse
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


BLOCKCHAIN_CHARTS_BASE_URL = "https://api.blockchain.info/charts"
BINANCE_MARKET_DATA_BASE_URL = "https://data-api.binance.vision"
DEFAULT_TIMEOUT_SECONDS = 30


def utc_now_iso() -> str:
    now = datetime.now(timezone.utc)
    return now.isoformat(timespec="milliseconds").replace("+00:00", "Z")


@dataclass(frozen=True)
class RawFetchResult:
    source: str
    symbol: str
    interval: str
    requested_at: str
    endpoint: str
    params: dict[str, Any]
    payload: Any


class BlockchainChartsSource:
    """Client for the official Blockchain.info Charts API."""

    def __init__(self, timeout: int = DEFAULT_TIMEOUT_SECONDS):
        self.timeout = timeout

    def fetch_market_price(
        self,
        *,
        chart_name: str = "market-price",
        symbol: str = "BTCUSD",
        timespan: str = "all",
        start: str | None = None,
        sampled: bool = False,
    ) -> RawFetchResult:
        endpoint = f"{BLOCKCHAIN_CHARTS_BASE_URL}/{chart_name}"
        params: dict[str, Any] = {
            "timespan": timespan,
            "format": "json",
            "sampled": str(sampled).lower(),
        }
        if start:
            params["start"] = start.split("T", 1)[0]

        query_string = urllib.parse.urlencode(params)
        url = f"{endpoint}?{query_string}"
        try:
            with urllib.request.urlopen(url, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception as e:
            raise RuntimeError(f"BlockchainCharts fetch error: {e}") from e

        return RawFetchResult(
            source="blockchain_charts_market_price",
            symbol=symbol,
            interval="1d",
            requested_at=utc_now_iso(),
            endpoint=endpoint,
            params=params,
            payload=payload,
        )


class BinanceMarketDataSource:
    """Client for public Binance market data via the official market-data endpoint."""

    def __init__(
        self,
        timeout: int = DEFAULT_TIMEOUT_SECONDS,
        base_url: str = BINANCE_MARKET_DATA_BASE_URL,
    ):
        self.timeout = timeout
        self.base_url = base_url.rstrip("/")

    def fetch_klines(
        self,
        *,
        symbol: str = "BTCUSDT",
        interval: str = "1d",
        start_time_ms: int | None = None,
        end_time_ms: int | None = None,
        limit: int = 1000,
    ) -> RawFetchResult:
        endpoint = f"{self.base_url}/api/v3/klines"
        effective_limit = min(limit, 1000)
        all_rows: list[list[Any]] = []
        cursor = start_time_ms

        while True:
            params: dict[str, Any] = {
                "symbol": symbol.upper(),
                "interval": interval,
                "limit": effective_limit,
            }
            if cursor is not None:
                params["startTime"] = cursor
            if end_time_ms is not None:
                params["endTime"] = end_time_ms

            query_string = urllib.parse.urlencode(params)
            url = f"{endpoint}?{query_string}"
            try:
                with urllib.request.urlopen(url, timeout=self.timeout) as response:
                    batch = json.loads(response.read().decode("utf-8"))
            except Exception as e:
                raise RuntimeError(f"Binance fetch error: {e}") from e

            if not batch:
                break

            all_rows.extend(batch)

            if len(batch) < effective_limit:
                break

            next_open_time = int(batch[-1][0])
            if cursor is not None and next_open_time <= cursor:
                break
            cursor = next_open_time + 1

            if end_time_ms is not None and cursor > end_time_ms:
                break

        return RawFetchResult(
            source="binance_klines",
            symbol=symbol.upper(),
            interval=interval,
            requested_at=utc_now_iso(),
            endpoint=endpoint,
            params={
                "symbol": symbol.upper(),
                "interval": interval,
                "startTime": start_time_ms,
                "endTime": end_time_ms,
                "limit": effective_limit,
            },
            payload=all_rows,
        )
