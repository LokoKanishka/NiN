from verticals.bitnin.services.bitnin_episode_builder.merge import merge_episode
from verticals.bitnin.services.bitnin_episode_builder.windows import build_episode_window
from verticals.bitnin.tests.conftest import load_fixture


def test_merge_episode_market_and_narrative():
    market = load_fixture("episode_market_sample.json")
    narrative = load_fixture("episode_narrative_sample.json")
    window = build_episode_window(total_bars=len(market), trigger_index=4, pre_bars=3, post_bars=7)
    episode = merge_episode(
        market_bars=market,
        narrative_events=narrative,
        trigger_index=4,
        trigger_types=["return", "narrative_reinforced", "volume_anomaly"],
        trigger_strength=2.0,
        window=window,
        dataset_version="fixture-episodes",
        market_source_ref="market.jsonl",
        narrative_source_ref="narrative.jsonl",
    )
    assert episode["narrative_signature"]["event_count"] == 2
    assert episode["status"] == "confirmed"
    assert episode["sources"]
