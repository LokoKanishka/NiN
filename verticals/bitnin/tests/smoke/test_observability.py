from __future__ import annotations

import pytest
from pathlib import Path
from verticals.bitnin.services.bitnin_observability.health import HealthChecker
from verticals.bitnin.services.bitnin_observability.audit import Auditor
from verticals.bitnin.services.bitnin_observability.snapshot import Snapshorter
from verticals.bitnin.services.bitnin_observability.builder import ObservabilityBuilder


def test_health_checker_initialization():
    checker = HealthChecker("http://n8n", "http://ollama", "http://qdrant")
    assert checker.n8n_url == "http://n8n"


def test_auditor_logging(tmp_path: Path):
    auditor = Auditor(tmp_path)
    entry = auditor.log("test_action", "test_actor", {"key": "value"})
    assert entry["action"] == "test_action"
    assert (tmp_path / f"audit_{entry['timestamp'].split('T')[0]}.jsonl").exists()


def test_snapshot_creation(tmp_path: Path):
    snap = Snapshorter(tmp_path)
    payload = {"state": "active"}
    path = snap.write_snapshot(payload, "mission_1")
    assert path.exists()
    assert "mission_1" in path.name


def test_builder_orchestration(tmp_path: Path):
    builder = ObservabilityBuilder(tmp_path)
    state = {"foo": "bar"}
    snapshot_path = builder.capture_standard_snapshot("test_mission", state)
    assert snapshot_path.exists()
    assert (tmp_path / "audits").exists()
    assert (tmp_path / "snapshots").exists()
