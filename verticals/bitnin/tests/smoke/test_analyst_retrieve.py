from pathlib import Path

from verticals.bitnin.services.bitnin_analyst.retrieve import AnalystRetriever


class FakeEmbedder:
    def embed_texts(self, texts):
        return [[0.1, 0.2, 0.3] for _ in texts]


class FakeQdrant:
    def search(self, *, collection, vector, limit, query_filter):
        if collection == "bitnin_episodes":
            return [
                {
                    "score": 0.71,
                    "payload": {
                        "episode_id": "ep_a",
                        "summary_local": "Episodio con breakout.",
                        "dominant_cause": "etf_institucional",
                    },
                }
            ]
        return [
            {
                "score": 0.66,
                "payload": {
                    "event_id": "evt_a",
                    "summary_local": "Evento ETF.",
                    "topics": ["etf_institucional"],
                },
            }
        ]


def test_analyst_retriever_logs_queries(tmp_path):
    retriever = AnalystRetriever(embedder=FakeEmbedder(), qdrant=FakeQdrant(), raw_root=tmp_path)
    context = {
        "market_state": {
            "symbol": "BTCUSDT",
            "interval": "1d",
            "return_1d": 0.01,
            "return_3d": 0.03,
            "return_7d": 0.06,
            "volatility_regime": "medium",
            "breakout": True,
            "volume_anomaly": True,
        },
        "recent_narrative": {
            "top_topics": ["etf_institucional"],
            "top_entities": ["Bitcoin"],
            "max_relevance_btc": 0.7,
        },
        "dataset_versions": {
            "episodes": "episodes-v0-real",
            "narrative": "narrative-v0-gdelt",
        },
    }
    result = retriever.retrieve(analysis_id="abc123", context=context)
    assert len(result["query_refs"]) == 2
    assert Path(result["query_refs"][0]).exists()
    assert result["episode_results"][0]["payload"]["episode_id"] == "ep_a"

