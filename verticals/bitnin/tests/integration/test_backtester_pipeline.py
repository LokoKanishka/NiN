import json
from pathlib import Path

from verticals.bitnin.services.bitnin_backtester.builder import BitNinBacktester
from verticals.bitnin.tests.conftest import load_fixture


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


class FakeAnalyst:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def build(self, *, symbol="BTCUSDT", interval="1d", as_of=None, top_k_episodes=5, top_k_events=5):
        analysis_id = as_of.replace(":", "").replace("-", "").replace(".", "").replace("Z", "")[-24:]
        path = self.root / f"{analysis_id}.json"
        payload = {
            "analysis_id": analysis_id,
            "timestamp": as_of,
            "market_state": {
                "symbol": symbol,
                "interval": interval,
                "as_of": as_of,
                "close": 71212.0,
                "return_1d": 0.01,
                "return_3d": 0.03,
                "return_7d": 0.05,
                "volatility_regime": "low",
                "breakout": True,
                "volume_anomaly": False,
                "summary": "BTCUSDT test state",
            },
            "dominant_hypothesis": "Cobertura insuficiente para accion direccional.",
            "supporting_factors": ["Breakout"],
            "counterarguments": ["Poca memoria util"],
            "retrieved_episodes": [
                {
                    "episode_id": "ep_a",
                    "score": 0.72,
                    "summary_local": "Episodio similar.",
                    "dominant_cause": "market_only",
                }
            ],
            "confidence": 0.4,
            "recommended_action": "no_trade",
            "risk_level": "unknown",
            "why_now": ["Mercado en observacion."],
            "why_not": ["Cobertura insuficiente."],
            "data_coverage_score": 1.0,
            "narrative_coverage_score": 0.2,
            "final_status": "insufficient_evidence",
            "model_name": "fake-model",
            "prompt_version": "fake-prompt",
            "dataset_versions": {
                "market": "market-v0-binance-1d",
                "narrative": "narrative-v0-gdelt",
                "episodes": "episodes-v0-real",
            },
            "query_refs": [],
            "notes": [],
        }
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return {
            "analysis_id": analysis_id,
            "normalized_path": str(path),
        }


def test_backtester_pipeline_runs_short_replay(tmp_path):
    market_path = tmp_path / "market.jsonl"
    _write_jsonl(market_path, load_fixture("analyst_market_sample.json"))
    analyst = FakeAnalyst(tmp_path / "analyses")
    backtester = BitNinBacktester(
        analyst=analyst,
        market_path=market_path,
        runs_root=tmp_path / "runs",
        reports_root=tmp_path / "reports",
        replays_root=tmp_path / "replays",
        snapshot_root=tmp_path / "snapshots",
    )
    result = backtester.run(symbol="BTCUSDT", interval="1d", warmup_bars=7, max_steps=2)
    report = json.loads(Path(result["report_path"]).read_text(encoding="utf-8"))

    assert Path(result["run_path"]).exists()
    assert Path(result["replay_path"]).exists()
    assert report["metrics"]["analysis_count"] == 2
    assert report["metrics"]["no_trade_count"] == 2

