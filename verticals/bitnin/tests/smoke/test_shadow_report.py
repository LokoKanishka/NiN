from pathlib import Path

from verticals.bitnin.services.bitnin_shadow.intent import build_shadow_intent
from verticals.bitnin.services.bitnin_shadow.report import build_shadow_report, write_shadow_report
from verticals.bitnin.tests.conftest import load_fixture


def test_shadow_report_persistence(tmp_path):
    analysis = load_fixture("shadow_analysis_sample.json")
    intent = build_shadow_intent(analysis=analysis, reasoning_ref="/tmp/analysis.json")
    report = build_shadow_report(analysis=analysis, intent=intent)
    path = write_shadow_report(path=tmp_path / "report.md", report_text=report)
    assert path.exists()
    assert "Shadow Intent" in path.read_text(encoding="utf-8")

