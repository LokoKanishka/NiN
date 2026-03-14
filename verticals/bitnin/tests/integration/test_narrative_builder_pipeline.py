import json

from verticals.bitnin.services.bitnin_narrative_builder.builder import NarrativeDatasetBuilder
from verticals.bitnin.services.bitnin_narrative_builder.sources import RawNarrativeFetchResult
from verticals.bitnin.tests.conftest import load_fixture


def test_narrative_builder_persists_pipeline(monkeypatch, tmp_path):
    builder = NarrativeDatasetBuilder()

    raw_dir = tmp_path / "raw"
    normalized_dir = tmp_path / "normalized"
    snapshots_dir = tmp_path / "snapshots"
    logs_dir = tmp_path / "logs"
    for path in (raw_dir, normalized_dir, snapshots_dir, logs_dir):
        path.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr("verticals.bitnin.services.bitnin_narrative_builder.builder.RAW_ROOT", raw_dir)
    monkeypatch.setattr("verticals.bitnin.services.bitnin_narrative_builder.builder.NORMALIZED_ROOT", normalized_dir)
    monkeypatch.setattr("verticals.bitnin.services.bitnin_narrative_builder.builder.SNAPSHOT_ROOT", snapshots_dir)
    monkeypatch.setattr("verticals.bitnin.services.bitnin_narrative_builder.builder.LOG_ROOT", logs_dir)

    fixture = RawNarrativeFetchResult(
        source="gdelt_doc_artlist",
        query="bitcoin",
        requested_at="2026-03-13T00:00:00.000Z",
        endpoint="https://api.gdeltproject.org/api/v2/doc/doc",
        params={"query": "bitcoin", "mode": "artlist", "format": "json"},
        payload=load_fixture("gdelt_doc_artlist_sample.json"),
    )

    class FakeSource:
        def fetch_articles(self, **kwargs):
            return fixture

    monkeypatch.setattr(
        "verticals.bitnin.services.bitnin_narrative_builder.builder.GDELTDocSource",
        lambda: FakeSource(),
    )

    result = builder.build_gdelt(dataset_version="fixture-v1", query="bitcoin")
    raw_payload = json.loads(next(raw_dir.iterdir()).read_text(encoding="utf-8"))
    normalized_lines = (
        normalized_dir / "gdelt_doc_artlist__bitcoin__fixture-v1.jsonl"
    ).read_text(encoding="utf-8").splitlines()
    snapshot_files = list(snapshots_dir.iterdir())

    assert result.event_count == 3
    assert raw_payload["source"] == "gdelt_doc_artlist"
    assert len(normalized_lines) == 3
    assert len(snapshot_files) == 1
