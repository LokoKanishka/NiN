from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from verticals.bitnin.services.bitnin_analyst.context import parse_utc


def read_market_bars(*, market_path: Path, symbol: str, interval: str) -> list[dict[str, Any]]:
    rows = [json.loads(line) for line in market_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    bars = [row for row in rows if row.get("symbol") == symbol and row.get("interval") == interval]
    return sorted(bars, key=lambda item: item["open_time"])


def build_replay_points(
    *,
    market_path: Path,
    symbol: str,
    interval: str,
    warmup_bars: int = 8,
    start: str | None = None,
    end: str | None = None,
    max_steps: int | None = None,
) -> list[dict[str, Any]]:
    bars = read_market_bars(market_path=market_path, symbol=symbol, interval=interval)
    replay_points: list[dict[str, Any]] = []
    for index, bar in enumerate(bars):
        if index + 1 < warmup_bars:
            continue
        close_time = parse_utc(bar["close_time"])
        if start and close_time < parse_utc(start):
            continue
        if end and close_time > parse_utc(end):
            continue
        replay_points.append(
            {
                "index": index,
                "timestamp": bar["close_time"],
                "bar": bar,
            }
        )
    if max_steps is not None:
        replay_points = replay_points[-max_steps:]
    return replay_points

