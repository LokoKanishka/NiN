import json
from pathlib import Path

from verticals.bitnin.services.bitnin_shadow.builder import BitNinShadowRunner
from verticals.bitnin.tests.conftest import load_fixture


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


class FakeAnalyst:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def build(self, *, symbol="BTCUSDT", interval="1d", top_k_episodes=5, top_k_events=5, as_of=None):
        analysis = load_fixture("shadow_analysis_sample.json")
        path = self.root / "analysis.json"
        path.write_text(json.dumps(analysis, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return {
            "analysis_id": analysis["analysis_id"],
            "normalized_path": str(path),
        }


def test_shadow_pipeline_end_to_end(tmp_path):
    market_path = tmp_path / "market.jsonl"
    _write_jsonl(market_path, load_fixture("analyst_market_sample.json"))
    runner = BitNinShadowRunner(
        analyst=FakeAnalyst(tmp_path / "analyses"),
        market_path=market_path,
        intents_root=tmp_path / "intents",
        reports_root=tmp_path / "reports",
        reviews_root=tmp_path / "reviews",
        snapshots_root=tmp_path / "snapshots",
    )
    run_result = runner.run(symbol="BTCUSDT", interval="1d")
    review_result = runner.review_intent(intent_path=run_result["intent_path"])
    intent = json.loads(Path(run_result["intent_path"]).read_text(encoding="utf-8"))
    review = json.loads(Path(review_result["review_path"]).read_text(encoding="utf-8"))

    assert Path(run_result["report_path"]).exists()
    assert Path(run_result["snapshot_path"]).exists()
    assert intent["status"] == "reviewed"
    assert review["suggested_action"] == "no_trade"

