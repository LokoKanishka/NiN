from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    REPO_ROOT = Path(__file__).resolve().parents[4]
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    from verticals.bitnin.services.bitnin_dataset_builder.normalize import (  # type: ignore
        interval_to_delta,
        normalize_binance_klines,
        normalize_blockchain_market_price,
        parse_utc_datetime,
        to_utc_string,
    )
    from verticals.bitnin.services.bitnin_dataset_builder.snapshot import write_snapshot  # type: ignore
    from verticals.bitnin.services.bitnin_dataset_builder.sources import (  # type: ignore
        BinanceMarketDataSource,
        BlockchainChartsSource,
        RawFetchResult,
    )
    from verticals.bitnin.services.bitnin_dataset_builder.validate import validate_market_bars  # type: ignore
else:
    from .normalize import (
        interval_to_delta,
        normalize_binance_klines,
        normalize_blockchain_market_price,
        parse_utc_datetime,
        to_utc_string,
    )
    from .snapshot import write_snapshot
    from .sources import BinanceMarketDataSource, BlockchainChartsSource, RawFetchResult
    from .validate import validate_market_bars


BITNIN_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_ROOT = BITNIN_ROOT / "runtime"
RAW_ROOT = RUNTIME_ROOT / "datasets" / "market" / "raw"
NORMALIZED_ROOT = RUNTIME_ROOT / "datasets" / "market" / "normalized"
SNAPSHOT_ROOT = RUNTIME_ROOT / "datasets" / "market" / "snapshots"
LOG_ROOT = RUNTIME_ROOT / "logs"


@dataclass
class BuildResult:
    source: str
    symbol: str
    interval: str
    dataset_version: str
    mode: str
    record_count: int
    raw_path: str
    normalized_path: str
    snapshot_path: str
    log_path: str
    validation: dict[str, Any]


class MarketDatasetBuilder:
    def __init__(self) -> None:
        for path in (RAW_ROOT, NORMALIZED_ROOT, SNAPSHOT_ROOT, LOG_ROOT):
            path.mkdir(parents=True, exist_ok=True)

    def build_blockchain_market_price(
        self,
        *,
        dataset_version: str,
        mode: str = "full",
        symbol: str = "BTCUSD",
        timespan: str = "all",
        start: str | None = None,
        sampled: bool = False,
    ) -> BuildResult:
        normalized_path = self._normalized_path("blockchain_charts_market_price", symbol, "1d", dataset_version)
        existing_records = self._read_jsonl(normalized_path) if mode == "incremental" else []
        effective_start = start or self._next_start(existing_records, "1d")

        raw_result = BlockchainChartsSource().fetch_market_price(
            symbol=symbol,
            timespan=timespan,
            start=effective_start,
            sampled=sampled,
        )
        raw_path = self._write_raw(raw_result)

        fresh_records = normalize_blockchain_market_price(
            raw_result,
            dataset_version=dataset_version,
            symbol=symbol,
        )
        merged_records = self._merge_records(existing_records, fresh_records)
        validation = validate_market_bars(merged_records)
        if not validation["valid"]:
            raise ValueError(json.dumps(validation, indent=2, ensure_ascii=False))

        self._write_jsonl(normalized_path, merged_records)
        snapshot_path = write_snapshot(
            snapshot_dir=SNAPSHOT_ROOT,
            dataset_version=dataset_version,
            source=raw_result.source,
            symbol=symbol,
            interval="1d",
            records=merged_records,
            validation_report=validation,
        )
        log_path = self._write_run_log(
            {
                "action": "build_blockchain_market_price",
                "mode": mode,
                "dataset_version": dataset_version,
                "symbol": symbol,
                "interval": "1d",
                "raw_path": str(raw_path),
                "normalized_path": str(normalized_path),
                "snapshot_path": str(snapshot_path),
                "validation": validation,
                "request": raw_result.params,
            }
        )
        return BuildResult(
            source=raw_result.source,
            symbol=symbol,
            interval="1d",
            dataset_version=dataset_version,
            mode=mode,
            record_count=len(merged_records),
            raw_path=str(raw_path),
            normalized_path=str(normalized_path),
            snapshot_path=str(snapshot_path),
            log_path=str(log_path),
            validation=validation,
        )

    def build_binance_klines(
        self,
        *,
        dataset_version: str,
        mode: str = "full",
        symbol: str = "BTCUSDT",
        interval: str = "1d",
        start: str | None = None,
        end: str | None = None,
        limit: int = 1000,
    ) -> BuildResult:
        interval_to_delta(interval)
        normalized_path = self._normalized_path("binance_klines", symbol, interval, dataset_version)
        existing_records = self._read_jsonl(normalized_path) if mode == "incremental" else []
        effective_start = start or self._next_start(existing_records, interval)
        start_ms = self._iso_to_millis(effective_start) if effective_start else None
        end_ms = self._iso_to_millis(end) if end else None

        raw_result = BinanceMarketDataSource().fetch_klines(
            symbol=symbol,
            interval=interval,
            start_time_ms=start_ms,
            end_time_ms=end_ms,
            limit=limit,
        )
        raw_path = self._write_raw(raw_result)

        fresh_records = normalize_binance_klines(raw_result, dataset_version=dataset_version)
        merged_records = self._merge_records(existing_records, fresh_records)
        validation = validate_market_bars(merged_records)
        if not validation["valid"]:
            raise ValueError(json.dumps(validation, indent=2, ensure_ascii=False))

        self._write_jsonl(normalized_path, merged_records)
        snapshot_path = write_snapshot(
            snapshot_dir=SNAPSHOT_ROOT,
            dataset_version=dataset_version,
            source=raw_result.source,
            symbol=symbol,
            interval=interval,
            records=merged_records,
            validation_report=validation,
        )
        log_path = self._write_run_log(
            {
                "action": "build_binance_klines",
                "mode": mode,
                "dataset_version": dataset_version,
                "symbol": symbol,
                "interval": interval,
                "raw_path": str(raw_path),
                "normalized_path": str(normalized_path),
                "snapshot_path": str(snapshot_path),
                "validation": validation,
                "request": raw_result.params,
            }
        )
        return BuildResult(
            source=raw_result.source,
            symbol=symbol,
            interval=interval,
            dataset_version=dataset_version,
            mode=mode,
            record_count=len(merged_records),
            raw_path=str(raw_path),
            normalized_path=str(normalized_path),
            snapshot_path=str(snapshot_path),
            log_path=str(log_path),
            validation=validation,
        )

    def _write_raw(self, raw_result: RawFetchResult) -> Path:
        safe_requested_at = raw_result.requested_at.replace(":", "-")
        filename = f"{raw_result.source}__{raw_result.symbol}__{raw_result.interval}__{safe_requested_at}.json"
        path = RAW_ROOT / filename
        payload = {
            "source": raw_result.source,
            "symbol": raw_result.symbol,
            "interval": raw_result.interval,
            "requested_at": raw_result.requested_at,
            "endpoint": raw_result.endpoint,
            "params": raw_result.params,
            "payload": raw_result.payload,
        }
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return path

    def _write_jsonl(self, path: Path, records: list[dict[str, Any]]) -> None:
        lines = [json.dumps(record, ensure_ascii=False, sort_keys=True) for record in records]
        path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")

    def _read_jsonl(self, path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        rows: list[dict[str, Any]] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
        return rows

    def _merge_records(
        self,
        existing_records: list[dict[str, Any]],
        new_records: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        merged: dict[tuple[str, str, str], dict[str, Any]] = {}
        for record in existing_records + new_records:
            key = (record["symbol"], record["interval"], record["open_time"])
            merged[key] = record
        return sorted(merged.values(), key=lambda item: (item["symbol"], item["interval"], item["open_time"]))

    def _normalized_path(self, source: str, symbol: str, interval: str, dataset_version: str) -> Path:
        filename = f"{source}__{symbol}__{interval}__{dataset_version}.jsonl"
        return NORMALIZED_ROOT / filename

    def _next_start(self, existing_records: list[dict[str, Any]], interval: str) -> str | None:
        if not existing_records:
            return None
        latest_open = max(parse_utc_datetime(record["open_time"]) for record in existing_records)
        return to_utc_string(latest_open + interval_to_delta(interval))

    def _write_run_log(self, payload: dict[str, Any]) -> Path:
        log_name = f"bitnin_dataset_builder__{payload['action']}__{payload['dataset_version']}__{payload['symbol']}__{payload['interval']}.json"
        path = LOG_ROOT / log_name
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return path

    def _iso_to_millis(self, value: str) -> int:
        dt = parse_utc_datetime(value)
        return int(dt.timestamp() * 1000)


def build_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="BitNin market dataset builder")
    subparsers = parser.add_subparsers(dest="command", required=True)

    blockchain = subparsers.add_parser("blockchain", help="Build canonical daily dataset from Blockchain.com")
    blockchain.add_argument("--dataset-version", required=True)
    blockchain.add_argument("--mode", choices=["full", "incremental"], default="full")
    blockchain.add_argument("--symbol", default="BTCUSD")
    blockchain.add_argument("--timespan", default="all")
    blockchain.add_argument("--start")
    blockchain.add_argument("--sampled", action="store_true")

    binance = subparsers.add_parser("binance", help="Build OHLCV dataset from Binance public klines")
    binance.add_argument("--dataset-version", required=True)
    binance.add_argument("--mode", choices=["full", "incremental"], default="full")
    binance.add_argument("--symbol", default="BTCUSDT")
    binance.add_argument("--interval", choices=["1d", "4h", "1h"], default="1d")
    binance.add_argument("--start")
    binance.add_argument("--end")
    binance.add_argument("--limit", type=int, default=1000)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_cli_parser()
    args = parser.parse_args(argv)
    builder = MarketDatasetBuilder()

    if args.command == "blockchain":
        result = builder.build_blockchain_market_price(
            dataset_version=args.dataset_version,
            mode=args.mode,
            symbol=args.symbol,
            timespan=args.timespan,
            start=args.start,
            sampled=args.sampled,
        )
    else:
        result = builder.build_binance_klines(
            dataset_version=args.dataset_version,
            mode=args.mode,
            symbol=args.symbol,
            interval=args.interval,
            start=args.start,
            end=args.end,
            limit=args.limit,
        )

    print(json.dumps(asdict(result), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
