import json
from pathlib import Path

from verticals.bitnin.services.bitnin_analyst.builder import BitNinAnalyst
from verticals.bitnin.services.bitnin_analyst.context import CurrentContextBuilder
from verticals.bitnin.services.bitnin_analyst.llm import LLMResult
from verticals.bitnin.tests.conftest import load_fixture


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


class FakeRetriever:
    def __init__(self, query_refs):
        self.query_refs = query_refs

    def retrieve(self, *, analysis_id, context, top_k_episodes=5, top_k_events=5):
        return {
            "queries": {"episodes": "btc breakout", "events": "bitcoin etf"},
            "episode_results": [
                {
                    "score": 0.73,
                    "payload": {
                        "episode_id": "ep_a",
                        "summary_local": "Episodio con breakout y narrativa ETF.",
                        "dominant_cause": "etf_institucional",
                    },
                },
                {
                    "score": 0.68,
                    "payload": {
                        "episode_id": "ep_b",
                        "summary_local": "Episodio con volatilidad alta.",
                        "dominant_cause": "geopolitica",
                    },
                },
            ],
            "event_results": [
                {
                    "score": 0.6,
                    "payload": {
                        "event_id": "evt_a",
                        "summary_local": "Evento ETF",
                        "topics": ["etf_institucional"],
                    },
                }
            ],
            "query_refs": self.query_refs,
        }


class FakeLLM:
    model = "qwen2.5:14b"

    def analyze(self, *, messages):
        return LLMResult(
            model_name=self.model,
            raw_response={"message": {"content": "ok"}},
            parsed_output={
                "dominant_hypothesis": "Momentum alcista con apoyo narrativo moderado.",
                "supporting_factors": ["Breakout reciente", "Analogos con continuidad"],
                "counterarguments": ["La narrativa todavia es parcial"],
                "confidence": 0.58,
                "recommended_action": "observe",
                "risk_level": "medium",
                "why_now": ["Se combinan breakout y volumen."],
                "why_not": ["No hay suficiente evidencia para ejecutar nada."],
                "final_status": "ok",
                "notes": ["Salida provisional."]
            },
        )


def test_analyst_builder_pipeline_with_mocks(tmp_path):
    market_path = tmp_path / "market.jsonl"
    narrative_path = tmp_path / "narrative.jsonl"
    episodes_path = tmp_path / "episodes.jsonl"
    query_a = tmp_path / "query_a.json"
    query_b = tmp_path / "query_b.json"
    query_a.write_text("{}", encoding="utf-8")
    query_b.write_text("{}", encoding="utf-8")
    _write_jsonl(market_path, load_fixture("analyst_market_sample.json"))
    _write_jsonl(narrative_path, load_fixture("analyst_narrative_sample.json"))
    _write_jsonl(episodes_path, load_fixture("analyst_episodes_sample.json"))

    analyst = BitNinAnalyst(
        context_builder=CurrentContextBuilder(
            market_path=market_path,
            narrative_path=narrative_path,
            episodes_path=episodes_path,
        ),
        retriever=FakeRetriever([str(query_a), str(query_b)]),
        llm_client=FakeLLM(),
        raw_root=tmp_path / "raw",
        normalized_root=tmp_path / "normalized",
        snapshot_root=tmp_path / "snapshots",
    )
    result = analyst.build(symbol="BTCUSDT", interval="1d")
    normalized = json.loads(Path(result["normalized_path"]).read_text(encoding="utf-8"))

    assert normalized["analysis_id"] == result["analysis_id"]
    assert normalized["recommended_action"] == "observe"
    assert normalized["final_status"] == "ok"
    assert len(normalized["retrieved_episodes"]) == 2
