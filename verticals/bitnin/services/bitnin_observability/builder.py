from __future__ import annotations

import datetime
from pathlib import Path
from typing import Any

from verticals.bitnin.services.bitnin_observability.health import HealthChecker
from verticals.bitnin.services.bitnin_observability.audit import Auditor
from verticals.bitnin.services.bitnin_observability.reports import ReportGenerator
from verticals.bitnin.services.bitnin_observability.replay import ReplayManager
from verticals.bitnin.services.bitnin_observability.snapshot import Snapshorter


class ObservabilityBuilder:
    """Orchestrator for BitNin observability artifacts."""

    def __init__(self, runtime_dir: Path):
        self.runtime_dir = runtime_dir
        self.health = HealthChecker(
            n8n_url="http://localhost:5688",
            ollama_url="http://host.docker.internal:11434",
            qdrant_url="http://localhost:6333",
        )
        self.audit = Auditor(runtime_dir / "audits")
        self.reports = ReportGenerator(runtime_dir / "reports")
        self.replay = ReplayManager(runtime_dir / "replay")
        self.snapshots = Snapshorter(runtime_dir / "snapshots")

    def capture_standard_snapshot(self, mission_id: str, state: dict[str, Any]):
        """Runs health check, logs audit, and writes snapshot."""
        health_results = self.health.run_all()
        
        self.audit.log(
            action="observability_snapshot",
            actor="bitnin_observability_builder",
            details={"mission_id": mission_id, "health": health_results["overall"]}
        )
        
        snapshot_payload = {
            "mission_id": mission_id,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "health": health_results,
            "state": state
        }
        
        return self.snapshots.write_snapshot(snapshot_payload, mission_id)
