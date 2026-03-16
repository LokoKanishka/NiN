import json
from pathlib import Path

from verticals.bitnin.services.bitnin_observability.scorecard import ScorecardGenerator


def test_scorecard_detects_narrative_collapse(tmp_path):
    reports_dir = tmp_path / "reports"
    generator = ScorecardGenerator(str(reports_dir))
    
    mock_batch = {
        "batch_id": "test_batch",
        "total_runs": 10,
        "metrics_summary": {
            "average_narrative_coverage": 0.1,  # Below 0.2
            "runs_with_active_memory": 5,
            "composite_states": {"HIGH": 5, "DIVERGENT": 5},
            "causal_typologies": {}
        },
        "statuses": {}
    }
    
    batch_path = reports_dir / "batch_report__test_batch.json"
    batch_path.write_text(json.dumps(mock_batch))
    
    _, alerts = generator.generate(str(batch_path))
    assert any("narrative coverage critically low" in alert.lower() for alert in alerts)


def test_scorecard_detects_memory_collapse(tmp_path):
    reports_dir = tmp_path / "reports"
    generator = ScorecardGenerator(str(reports_dir))
    
    mock_batch = {
        "batch_id": "test_batch_2",
        "total_runs": 10,
        "metrics_summary": {
            "average_narrative_coverage": 0.5,
            "runs_with_active_memory": 0,  # 0 on 10 runs
            "composite_states": {"HIGH": 5, "DIVERGENT": 5},
            "causal_typologies": {}
        },
        "statuses": {}
    }
    
    batch_path = reports_dir / "batch_report__test_batch_2.json"
    batch_path.write_text(json.dumps(mock_batch))
    
    _, alerts = generator.generate(str(batch_path))
    assert any("no active memory retrieved" in alert.lower() for alert in alerts)


def test_scorecard_detects_state_collapse(tmp_path):
    reports_dir = tmp_path / "reports"
    generator = ScorecardGenerator(str(reports_dir))
    
    mock_batch = {
        "batch_id": "test_batch_3",
        "total_runs": 10,
        "metrics_summary": {
            "average_narrative_coverage": 0.5,
            "runs_with_active_memory": 5,
            "composite_states": {"DIVERGENT": 10, "HIGH": 0},  # 100% DIVERGENT
            "causal_typologies": {}
        },
        "statuses": {}
    }
    
    batch_path = reports_dir / "batch_report__test_batch_3.json"
    batch_path.write_text(json.dumps(mock_batch))
    
    _, alerts = generator.generate(str(batch_path))
    assert any("100% of runs collapsed" in alert.lower() for alert in alerts)
