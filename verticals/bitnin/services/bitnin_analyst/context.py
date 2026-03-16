from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import pstdev
from typing import Any


BITNIN_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MARKET_PATH = (
    BITNIN_ROOT / "runtime" / "datasets" / "market" / "normalized" / "binance_klines__BTCUSDT__1d__market-v0-binance-1d.jsonl"
)
DEFAULT_NARRATIVE_PATH = (
    BITNIN_ROOT / "runtime" / "datasets" / "narrative" / "normalized" / "gdelt_doc_artlist__bitcoin__narrative-v1-robust.jsonl"
)
DEFAULT_EPISODES_PATH = (
    BITNIN_ROOT / "runtime" / "datasets" / "episodes" / "normalized" / "episodes__BTCUSDT__1d__episodes-v0-real.jsonl"
)
POLICY_PATH = BITNIN_ROOT / "POLICY.md"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _return_ratio(current_close: float, past_close: float | None) -> float | str:
    if past_close in (None, 0):
        return "insufficient_history"
    return round((current_close / past_close) - 1, 6)


def _classify_volatility(returns: list[float]) -> str:
    if len(returns) < 3:
        return "unknown"
    vol_score = pstdev(abs(value) for value in returns[-7:])
    if vol_score >= 0.025:
        return "high"
    if vol_score >= 0.015:
        return "medium"
    return "low"


def _build_policy_context(policy_path: Path) -> list[str]:
    lines = []
    for raw_line in policy_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if "No ejecucion financiera en v1" in line:
            lines.append("No ejecucion financiera en v1.")
        elif "`no_trade` e `insufficient_evidence`" in line:
            lines.append("`no_trade` e `insufficient_evidence` son salidas validas del analista.")
        elif "Shadow y simulacion son los unicos modos validos en v1" in line:
            lines.append("Shadow y simulacion son los unicos modos validos en v1.")
    return lines


class CurrentContextBuilder:
    def __init__(
        self,
        *,
        market_path: Path | None = None,
        narrative_path: Path | None = None,
        episodes_path: Path | None = None,
        policy_path: Path | None = None,
        narrative_lookback_days: int = 7,
    ) -> None:
        self.market_path = market_path or DEFAULT_MARKET_PATH
        self.narrative_path = narrative_path or DEFAULT_NARRATIVE_PATH
        self.episodes_path = episodes_path or DEFAULT_EPISODES_PATH
        self.policy_path = policy_path or POLICY_PATH
        self.narrative_lookback_days = narrative_lookback_days

    def build(
        self,
        *,
        symbol: str = "BTCUSDT",
        interval: str = "1d",
        as_of: str | None = None,
        analysis_timestamp: str | None = None,
    ) -> dict[str, Any]:
        market_bars = [
            row
            for row in _read_jsonl(self.market_path)
            if row.get("symbol") == symbol and row.get("interval") == interval
        ]
        if as_of is not None:
            cutoff = parse_utc(as_of)
            market_bars = [
                row
                for row in market_bars
                if parse_utc(row["close_time"]) <= cutoff
            ]
        if not market_bars:
            raise ValueError(f"No market bars found for {symbol} {interval} in {self.market_path}")

        market_bars.sort(key=lambda item: item["open_time"])
        latest_bar = market_bars[-1]
        closes = [float(bar["close"]) for bar in market_bars]
        quote_volumes = [float(bar.get("quote_volume", 0.0) or 0.0) for bar in market_bars]
        daily_returns = [
            round((closes[index] / closes[index - 1]) - 1, 6)
            for index in range(1, len(closes))
            if closes[index - 1]
        ]

        recent_prior_closes = closes[-8:-1]
        recent_prior_quote_volumes = [value for value in quote_volumes[-8:-1] if value > 0]
        latest_quote_volume = quote_volumes[-1]
        quote_volume_mean = (
            sum(recent_prior_quote_volumes) / len(recent_prior_quote_volumes)
            if recent_prior_quote_volumes
            else 0.0
        )
        volume_anomaly_score = (
            round(latest_quote_volume / quote_volume_mean, 6)
            if quote_volume_mean > 0
            else 0.0
        )
        breakout = False
        if recent_prior_closes:
            breakout = closes[-1] > max(recent_prior_closes) or closes[-1] < min(recent_prior_closes)

        as_of_dt = parse_utc(as_of) if as_of is not None else parse_utc(latest_bar["close_time"])
        narrative_events = _read_jsonl(self.narrative_path)
        recent_narratives = [
            event
            for event in narrative_events
            if as_of_dt - timedelta(days=self.narrative_lookback_days)
            <= parse_utc(event["timestamp_start"])
            <= as_of_dt
        ]
        recent_narratives.sort(key=lambda item: item["timestamp_start"])

        topic_counter = Counter(topic for event in recent_narratives for topic in event.get("topics", []))
        entity_counter = Counter(entity for event in recent_narratives for entity in event.get("entities", []))
        relevance_values = [float(event.get("relevance_btc", 0.0)) for event in recent_narratives]
        avg_relevance = sum(relevance_values) / len(relevance_values) if relevance_values else 0.0
        narrative_coverage_score = 0.0
        if recent_narratives:
            narrative_coverage_score = round(min(1.0, avg_relevance * min(1.0, len(recent_narratives) / 3)), 6)

        episodes = [
            episode
            for episode in _read_jsonl(self.episodes_path)
            if parse_utc(episode["window_end"]) <= as_of_dt
        ]
        recent_episode_refs = [
            episode["episode_id"]
            for episode in sorted(episodes, key=lambda item: item["window_end"])[-3:]
        ]

        data_coverage_score = round(min(1.0, len(market_bars) / 8), 6)
        market_state = {
            "symbol": symbol,
            "interval": interval,
            "as_of": latest_bar["close_time"],
            "close": float(latest_bar["close"]),
            "return_1d": _return_ratio(closes[-1], closes[-2] if len(closes) >= 2 else None),
            "return_3d": _return_ratio(closes[-1], closes[-4] if len(closes) >= 4 else None),
            "return_7d": _return_ratio(closes[-1], closes[-8] if len(closes) >= 8 else None),
            "volatility_regime": _classify_volatility(daily_returns),
            "breakout": breakout,
            "volume_anomaly": volume_anomaly_score >= 1.8,
            "summary": (
                f"{symbol} {interval} close={float(latest_bar['close'])} "
                f"return_1d={_return_ratio(closes[-1], closes[-2] if len(closes) >= 2 else None)} "
                f"volatility={_classify_volatility(daily_returns)} "
                f"breakout={breakout} volume_anomaly={volume_anomaly_score >= 1.8}"
            ),
        }

        return {
            "analysis_timestamp": analysis_timestamp or (as_of if as_of is not None else utc_now_iso()),
            "market_state": market_state,
            "recent_narrative": {
                "event_count": len(recent_narratives),
                "top_topics": [topic for topic, _ in topic_counter.most_common(5)],
                "top_entities": [entity for entity, _ in entity_counter.most_common(5)],
                "max_relevance_btc": round(max(relevance_values), 6) if relevance_values else 0.0,
                "event_ids": [event["event_id"] for event in recent_narratives[-5:]],
            },
            "recent_episode_refs": recent_episode_refs,
            "retrieval_cutoff": (as_of or latest_bar["close_time"]),
            "policy_context": _build_policy_context(self.policy_path),
            "data_coverage_score": data_coverage_score,
            "narrative_coverage_score": narrative_coverage_score,
            "dataset_versions": {
                "market": latest_bar["dataset_version"],
                "narrative": recent_narratives[-1]["dataset_version"] if recent_narratives else "narrative:none",
                "episodes": episodes[-1]["dataset_version"] if episodes else "episodes:none",
            },
            "source_paths": {
                "market": str(self.market_path),
                "narrative": str(self.narrative_path),
                "episodes": str(self.episodes_path),
            },
            "active_memory": [],  # Filled by retriever later
        }
