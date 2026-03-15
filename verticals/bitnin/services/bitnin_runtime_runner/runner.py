"""
Runner for bitnin-runtime-runner.
Orchestrates the full BitNin pipeline.
"""
import uuid
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any

# Imports from other services
from verticals.bitnin.services.bitnin_analyst.builder import BitNinAnalyst
from verticals.bitnin.services.bitnin_analyst.context import (
    DEFAULT_MARKET_PATH,
    utc_now_iso
)
from verticals.bitnin.services.bitnin_shadow.builder import BitNinShadowRunner
from verticals.bitnin.services.bitnin_hitl.builder import BitNinHitlRunner
from verticals.bitnin.services.bitnin_exec_guard.builder import BitNinExecGuardRunner
from verticals.bitnin.services.bitnin_observability.builder import ObservabilityBuilder
from verticals.bitnin.services.bitnin_observability.health import HealthChecker

logger = logging.getLogger(__name__)

class BitNinRuntimeRunner:
    """
    Main orchestrator for BitNin operational cycles.
    """
    def __init__(self, root_dir: str = "/home/lucy-ubuntu/Escritorio/NIN/verticals/bitnin"):
        self.root = Path(root_dir)
        self.runtime_base = self.root / "runtime"
        
        # Initialize sub-runners with default paths
        self.analyst = BitNinAnalyst(
            normalized_root=self.runtime_base / "analyses/normalized",
            snapshot_root=self.runtime_base / "analyses/snapshots"
        )
        # Note: Analyst uses its own defaults for raw/query, and takes Path objects
        
        self.shadow = BitNinShadowRunner(
            intents_root=self.runtime_base / "shadow/intents",
            reports_root=self.runtime_base / "shadow/reports",
            snapshots_root=self.runtime_base / "shadow/snapshots",
            reviews_root=self.runtime_base / "shadow/reviews"
        )
        self.hitl = BitNinHitlRunner(
            requests_root=self.runtime_base / "approvals/requests",
            decisions_root=self.runtime_base / "approvals/decisions",
            snapshots_root=self.runtime_base / "approvals/snapshots"
        )
        self.exec_guard = BitNinExecGuardRunner(
            results_root=self.runtime_base / "execution/results",
            snapshots_root=self.runtime_base / "execution/snapshots",
            logs_root=self.runtime_base / "execution/logs"
        )
        self.obs = ObservabilityBuilder(runtime_dir=self.runtime_base / "observability")
        self.health = HealthChecker(
            n8n_url="http://localhost:5688",
            ollama_url="http://host.docker.internal:11434",
            qdrant_url="http://localhost:6333"
        )

    def run_once(self, symbol: str = "BTCUSDT", interval: str = "1d", top_k: int = 5, auto_approve: bool = False) -> Dict[str, Any]:
        """Runs a single iteration of the pipeline."""
        replay_id = f"op_{uuid.uuid4().hex[:8]}"
        points = []
        
        def log_point(event: str, data: Any):
            points.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event": event,
                "data": data
            })

        logger.info(f"Starting BitNin Operational Cycle: {replay_id}")

        # 1. Health Check
        health_status = self.health.run_all()
        log_point("health_check", health_status)
        
        if health_status["overall"] == "DEGRADED":
            logger.warning("System degraded. Proceeding with caution.")

        try:
            # 2. Analyst
            logger.info(f"Invoking Analyst for {symbol} {interval}")
            analysis_res = self.analyst.build(symbol=symbol, interval=interval, top_k_episodes=top_k)
            log_point("analyst", {"path": analysis_res["normalized_path"]})
            
            # 3. Shadow
            logger.info("Generating Shadow Intent")
            shadow_res = self.shadow.run(symbol=symbol, interval=interval)
            hitl_res = self.hitl.request(
                intent_path=str(shadow_res["intent_path"]),
                expires_at=None
            )
            points.append({"timestamp": utc_now_iso(), "event": "hitl_request", "data": {"request_path": hitl_res["request_path"]}})
            
            # 4. Decider (Auto-approve)
            if auto_approve:
                logger.info("AUTO_APPROVE enabled. Forcing decision.")
                decision_res = self.hitl.decide(
                    approval_id=hitl_res["approval_id"],
                    decision="approved",
                    actor="runtime_runner_auto",
                    notes="Auto-approved by BitNinRuntimeRunner"
                )
                points.append({"timestamp": utc_now_iso(), "event": "hitl_decision", "data": {"decision_path": decision_res["decision_path"]}})
                approval_path = decision_res["decision_path"]
            else:
                approval_path = None

            # 5. Exec Guard
            if approval_path:
                logger.info("Running ExecGuard (Dry-Run)")
                exec_res = self.exec_guard.run(
                    intent_path=str(shadow_res["intent_path"]),
                    approval_path=approval_path,
                    analysis_path=analysis_res["normalized_path"]
                )
                points.append({"timestamp": utc_now_iso(), "event": "exec_guard", "data": {"record_path": exec_res["record_path"]}})
            
        except Exception as e:
            logger.error(f"Cycle failed: {e}")
            log_point("error", {"message": str(e)})
            # We don't re-raise to ensure observability is registered
        finally:
            # 6. Observability
            logger.info("Registering Observability Replay")
            self.obs.replay.register_replay(replay_id=replay_id, points=points)
            
        return {"replay_id": replay_id, "points": points}
