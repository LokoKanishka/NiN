from verticals.bitnin.services.bitnin_narrative_builder.dedupe import canonicalize_url, dedupe_narrative_events
from verticals.bitnin.services.bitnin_narrative_builder.normalize import normalize_gdelt_articles
from verticals.bitnin.services.bitnin_narrative_builder.sources import RawNarrativeFetchResult
from verticals.bitnin.tests.conftest import load_fixture


def test_canonicalize_url_removes_tracking_params():
    url = "https://example.com/path/article?utm_source=x&id=7#frag"
    assert canonicalize_url(url) == "https://example.com/path/article?id=7"


def test_dedupe_narrative_events_removes_url_and_title_time_duplicates():
    raw = RawNarrativeFetchResult(
        source="gdelt_doc_artlist",
        query="bitcoin",
        requested_at="2026-03-13T00:00:00.000Z",
        endpoint="https://api.gdeltproject.org/api/v2/doc/doc",
        params={"query": "bitcoin"},
        payload=load_fixture("gdelt_doc_artlist_sample.json"),
    )
    events = normalize_gdelt_articles(raw, dataset_version="fixture-v1")
    deduped = dedupe_narrative_events(events)
    assert len(deduped) == 3
