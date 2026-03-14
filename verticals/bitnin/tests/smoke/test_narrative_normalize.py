from verticals.bitnin.services.bitnin_narrative_builder.normalize import normalize_gdelt_articles, validate_narrative_events
from verticals.bitnin.services.bitnin_narrative_builder.sources import RawNarrativeFetchResult
from verticals.bitnin.tests.conftest import load_fixture


def test_normalize_gdelt_articles_fixture():
    raw = RawNarrativeFetchResult(
        source="gdelt_doc_artlist",
        query="bitcoin",
        requested_at="2026-03-13T00:00:00.000Z",
        endpoint="https://api.gdeltproject.org/api/v2/doc/doc",
        params={"query": "bitcoin", "mode": "artlist", "format": "json"},
        payload=load_fixture("gdelt_doc_artlist_sample.json"),
    )

    events = normalize_gdelt_articles(raw, dataset_version="fixture-v1")
    assert len(events) == 4
    assert events[0]["retention_mode"] == "metadata_only"
    assert events[0]["timestamp_start"].endswith("Z")
    assert "summary" not in events[0]

    report = validate_narrative_events(events)
    assert report["valid"] is True
