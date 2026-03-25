"""
Runner for bitnin-runtime-runner.
Orchestrates the full BitNin pipeline.
"""
import uuid
import logging
import json
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
            ollama_url="http://localhost:11434",
            qdrant_url="http://localhost:6335",
            searxng_url="http://localhost:8080"
        )

    def generate_batch_report(self, batch_id: str, results: list[Dict[str, Any]]) -> str:
        """Generates a summary report for a batch of runs with stability metrics."""
        stats = {
            "batch_id": batch_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_runs": len(results),
            "statuses": {},
            "outcomes": {
                "accepted_dry_run": 0,
                "no_trade": 0,
                "insufficient_evidence": 0,
                "error": 0
            },
            "durations": {
                "total": 0.0,
                "average": 0.0,
                "per_run": []
            },
            "health_summary": {
                "n8n": {"UP": 0, "DOWN": 0, "UNREACHABLE_BUT_NON_BLOCKING": 0},
                "ollama": {"UP": 0, "DOWN": 0, "UNREACHABLE_BUT_NON_BLOCKING": 0},
                "qdrant": {"UP": 0, "DOWN": 0, "UNREACHABLE_BUT_NON_BLOCKING": 0},
                "searxng": {"UP": 0, "DOWN": 0, "UNREACHABLE_BUT_NON_BLOCKING": 0}
            },
            "metrics_summary": {
                "composite_states": {"HIGH": 0, "DIVERGENT": 0, "LOW": 0},
                "causal_typologies": {},
                "average_narrative_coverage": 0.0,
                "runs_with_active_memory": 0,
                "ingestion_failures": 0
            },
            "detailed_runs": []
        }
        
        for res in results:
            run_id = res.get("replay_id")
            points = res.get("points", [])
            duration = res.get("duration", 0.0)
            
            # 1. Durations
            stats["durations"]["total"] += duration
            stats["durations"]["per_run"].append({"run_id": run_id, "duration": duration})
            
            # 2. Health aggregation
            for p in points:
                if p["event"] == "health_check":
                    for check in p["data"].get("checks", []):
                        svc = check["service"]
                        status = check["status"]
                        if svc in stats["health_summary"]:
                            if status in stats["health_summary"][svc]:
                                stats["health_summary"][svc][status] += 1
                            else:
                                stats["health_summary"][svc][status] = stats["health_summary"][svc].get(status, 0) + 1
            
            # 3. Outcome & Status categorization
            final_status = "unknown"
            outcome = "error"
            
            # Extract status from analyst or points
            analyst_status = res.get("analyst_status")
            analyst_action = res.get("analyst_action")
            
            has_exec = any(p["event"] == "exec_guard" for p in points)
            has_error = any(p["event"] == "error" for p in points)
            
            if has_exec:
                outcome = "accepted_dry_run"
                final_status = "executed"
            elif analyst_status == "insufficient_evidence":
                outcome = "insufficient_evidence"
                final_status = "insufficient_evidence"
            elif analyst_action == "no_trade":
                outcome = "no_trade"
                final_status = "no_trade"
            elif has_error:
                outcome = "error"
                final_status = "failed"
            else:
                # Fallback scan of points
                for p in reversed(points):
                    if p["event"] == "hitl_decision":
                        final_status = p["data"].get("decision", "decided")
                        break
                    if p["event"] == "error":
                        final_status = "failed"
                        break
            
            if outcome in stats["outcomes"]:
                stats["outcomes"][outcome] += 1
            
            # Additional detailed metrics extraction
            composite_state = res.get("composite_signal", {}).get("state", "UNKNOWN")
            if composite_state in stats["metrics_summary"]["composite_states"]:
                stats["metrics_summary"]["composite_states"][composite_state] += 1
            
            typology = res.get("composite_signal", {}).get("causal_typology", "UNKNOWN")
            stats["metrics_summary"]["causal_typologies"][typology] = stats["metrics_summary"]["causal_typologies"].get(typology, 0) + 1
            
            stats["metrics_summary"]["average_narrative_coverage"] += res.get("narrative_coverage_score", 0.0)
            if res.get("active_memory_count", 0) > 0:
                stats["metrics_summary"]["runs_with_active_memory"] += 1
            
            if res.get("ingestion_status") == "failed":
                stats["metrics_summary"]["ingestion_failures"] += 1

            stats["statuses"][final_status] = stats["statuses"].get(final_status, 0) + 1
            stats["detailed_runs"].append({
                "run_id": run_id,
                "status": final_status,
                "outcome": outcome,
                "duration": duration,
                "points_count": len(points),
                "composite_state": composite_state,
                "causal_typology": typology,
                "narrative_coverage": res.get("narrative_coverage_score", 0.0)
            })
        
        if stats["total_runs"] > 0:
            stats["durations"]["average"] = stats["durations"]["total"] / stats["total_runs"]
            stats["metrics_summary"]["average_narrative_coverage"] /= stats["total_runs"]
            
        report_path = self.runtime_base / "observability" / f"batch_report__{batch_id}.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(stats, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return str(report_path)

    def run_once(self, symbol: str = "BTCUSDT", interval: str = "1d", top_k: int = 5, auto_approve: bool = False, run_id: str | None = None, as_of: str | None = None, ingestion_status: str = "ok") -> Dict[str, Any]:
        """Runs a single iteration of the pipeline with instrumentation."""
        import time
        start_time = time.time()
        
        if not run_id:
            run_id = f"op_{uuid.uuid4().hex[:8]}"
        
        replay_id = run_id
        points = []
        analyst_status = "unknown"
        analyst_action = "unknown"
        analysis_res = {}
        
        def log_point(event: str, data: Any):
            points.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event": event,
                "data": data
            })

        logger.info(f"Starting BitNin Operational Cycle: {replay_id}")

        # 1. Health Check
        # analyst needs ollama, qdrant and searxng
        required_deps = ["ollama", "qdrant", "searxng"]
        health_status = self.health.run_all(required=required_deps)
        log_point("health_check", health_status)
        
        if health_status["overall"] == "DOWN":
            logger.error("Required dependencies are DOWN. Aborting cycle.")
            log_point("error", {"message": "Critical health failure", "details": health_status})
            return {"replay_id": replay_id, "points": points, "duration": 0.0, "analyst_status": "error", "analyst_action": "abort"}

        if health_status["overall"] == "DEGRADED":
            logger.warning("System degraded (non-blocking). Proceeding.")

        try:
            # 2. Analyst
            logger.info(f"Invoking Analyst for {symbol} {interval} with run_id {run_id} as_of {as_of}")
            analysis_res = self.analyst.build(symbol=symbol, interval=interval, top_k_episodes=top_k, run_id=run_id, as_of=as_of)
            analyst_status = analysis_res.get("final_status", "unknown")
            analyst_action = analysis_res.get("recommended_action", "unknown")
            log_point("analyst", {"path": analysis_res["normalized_path"], "status": analyst_status})
            
            # 3. Shadow
            logger.info("Generating Shadow Intent")
            shadow_res = self.shadow.run(symbol=symbol, interval=interval, run_id=run_id)
            hitl_res = self.hitl.request(
                intent_path=str(shadow_res["intent_path"]),
                expires_at=None,
                run_id=run_id
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
                    analysis_path=analysis_res["normalized_path"],
                    run_id=run_id
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
            
        duration = time.time() - start_time
        return {
            "replay_id": replay_id, 
            "points": points, 
            "duration": duration,
            "analyst_status": analyst_status,
            "analyst_action": analyst_action,
            "composite_signal": analysis_res.get("composite_signal", {}),
            "narrative_coverage_score": analysis_res.get("narrative_coverage_score", 0.0),
            "active_memory_count": len(analysis_res.get("active_memory", [])),
            "ingestion_status": ingestion_status
        }
