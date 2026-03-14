from verticals.bitnin.services.bitnin_memory_indexer.payloads import (
    episode_embedding_text,
    episode_payload,
    event_embedding_text,
    event_payload,
    stable_point_id,
)
from verticals.bitnin.tests.conftest import load_fixture


def test_episode_payload_and_text():
    episode = load_fixture("episode_builder_output_sample.json")[0]
    episode["market_source_ref"] = "binance_klines__BTCUSDT__1d__market-v0-binance-1d.jsonl"
    payload = episode_payload(episode)
    text = episode_embedding_text(episode)
    assert payload["episode_id"] == episode["episode_id"]
    assert payload["symbol"] == "BTCUSDT"
    assert "volatility_regime" in payload
    assert "dominant_cause=" in text


def test_event_payload_and_text():
    event = load_fixture("gdelt_doc_artlist_normalized_sample.json")[0]
    payload = event_payload(event)
    text = event_embedding_text(event)
    assert payload["event_id"] == event["event_id"]
    assert event["title"] in text


def test_stable_point_id_is_deterministic():
    assert stable_point_id("abc") == stable_point_id("abc")
