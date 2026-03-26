#!/usr/bin/env python3
import json
import logging
import os
import sys
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.run_shadow_pipeline import main as run_pipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("bitnin_supervisor")

class BitNinSupervisor:
    """Orchestrates sustained shadow operations, handles resumes, and prevents overlaps."""

    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        # Standard BitNin runtime path
        self.bitnin_dir = root_dir / "verticals" / "bitnin"
        self.obs_dir = self.bitnin_dir / "runtime" / "observability"
        self.state_path = self.obs_dir / "history" / "operational_state.json"
        self.lock_path = self.obs_dir / "history" / "bitnin_supervisor.lock"
        
        self.obs_dir.mkdir(parents=True, exist_ok=True)
        (self.obs_dir / "history").mkdir(parents=True, exist_ok=True)

    def _acquire_lock(self) -> bool:
        if self.lock_path.exists():
            # Check if process is still alive (minimal check)
            try:
                pid = int(self.lock_path.read_text())
                os.kill(pid, 0)
                logger.error(f"Execution blocked: Supervisor already running (PID {pid})")
                return False
            except (ProcessLookupError, ValueError, FileNotFoundError):
                logger.warning("Stale lock detected. Removing.")
                self.lock_path.unlink()
        
        self.lock_path.write_text(str(os.getpid()))
        return True

    def _release_lock(self):
        if self.lock_path.exists():
            self.lock_path.unlink()

    def load_state(self) -> dict:
        if self.state_path.exists():
            try:
                return json.loads(self.state_path.read_text())
            except Exception as e:
                logger.error(f"Failed to load state: {e}")
        return {
            "last_processed_date": None,
            "system_status": "UNKNOWN",
            "last_healthy_window": None,
            "active_alerts": [],
            "last_update": None
        }

    def save_state(self, state: dict):
        state["last_update"] = datetime.now(timezone.utc).isoformat()
        self.state_path.write_text(json.dumps(state, indent=2))
        self._generate_health_snapshot(state)

    def _generate_health_snapshot(self, state: dict):
        """Generates a human-readable markdown snapshot of the system health."""
        history_dir = self.obs_dir / "history" # Use history_dir for clarity
        snapshot_file = history_dir / "health_snapshot.md"
        json_snapshot_file = history_dir / "health_snapshot.json"
        
        now = datetime.now(timezone.utc) # Use timezone-aware datetime
        
        # Structure for JSON export
        json_data = {
            "timestamp": now.isoformat(),
            "status": "HEALTHY", # Default status
            "components": {},
            "freshness": {
                "last_run": state.get("last_processed_date", "Never"),
                "is_stale": False
            },
            "alerts": []
        }
        logger.info(f"Generating health snapshot at: {snapshot_file}")
        
        # Freshness Check for MD and JSON
        is_stale = False
        last_update_str = state.get("last_update")
        if last_update_str:
            last_update = datetime.fromisoformat(last_update_str)
            if now - last_update > timedelta(hours=25):
                is_stale = True
                json_data["freshness"]["is_stale"] = True
                json_data["status"] = "STALE"
                json_data["alerts"].append("STALE DATA: System hasn't processed successfully in > 25 hours.")
        
        md = f"# BitNin System Health Snapshot\n\n"
        md += f"**Last Update:** {last_update_str if last_update_str else 'N/A'}\n"
        
        status = state.get('system_status', 'UNKNOWN')
        if is_stale:
            status = "STALE (Possible Freeze)"
            md += f"**System Status:** ⚠️ {status}\n"
        else:
            status_icon = "🟢" if status == "HEALTHY" else "🔴" if status == "DEGRADED" else "🟡"
            md += f"**System Status:** {status_icon} {status}\n"
            json_data["status"] = status # Update JSON status based on system_status
            
        md += f"**Last Processed Date:** {state.get('last_processed_date', 'N/A')}\n"
        md += f"**Last Healthy Window:** {state.get('last_healthy_window', 'N/A')}\n\n"
        
        # Placeholder for 'last_batch' and 'metrics_summary' if they were to be added to state
        # For now, we'll use existing state info for components/metrics
        # If 'last_batch' was part of the state, it would be accessed like:
        # last_batch = state.get("last_batch_report", {})
        # metrics = last_batch.get("metrics_summary", {})
        # h_sum = last_batch.get("health_summary", {})
        
        # For now, let's just reflect the system_status in components for JSON
        json_data["components"]["overall_system"] = {"status": status}
        
        md += "## Active Alerts\n"
        alerts = state.get("active_alerts", [])
        if is_stale:
            md += f"- ⚠️ **STALE DATA**: System hasn't processed successfully in > 25 hours.\n"
        
        if not alerts and not is_stale:
            md += "- 🟢 All systems operational. No active alerts.\n"
        else:
            for alert in alerts:
                md += f"- {alert}\n"
                json_data["alerts"].append(alert) # Add alerts to JSON
        
        # Stale Check based on last_processed_date for MD (similar to original logic)
        last_date_str = state.get("last_processed_date")
        if last_date_str:
            last_date = datetime.strptime(last_date_str, "%Y-%m-%d")
            if (now.date() - last_date.date()).days > 2: # Compare dates only
                # This condition is already covered by the 25-hour check, but keeping it if it's a separate requirement
                if not json_data["freshness"]["is_stale"]: # Avoid duplicate stale status
                    json_data["freshness"]["is_stale"] = True
                    json_data["status"] = "STALE"
                    json_data["alerts"].append("WARNING: Last successful run was more than 48 hours ago.")
                md += "\n> [!WARNING]\n> **SISTEMA STALE**: Última corrida hace más de 48h.\n"
        
        md += "\n---\n*This file is ephemeral and reflects current operational state.*" # Reverted to original footer
        
        snapshot_file.write_text(md, encoding="utf-8")
        json_snapshot_file.write_text(json.dumps(json_data, indent=2))
        logger.info(f"Health snapshot updated (MD & JSON) at {now.isoformat()}")

    def run_sustained(self, start_date_str: str, days: int = 1):
        """Runs the pipeline for 'days' starting from start_date_str or the day after last_processed_date."""
        if not self._acquire_lock():
            return

        try:
            state = self.load_state()
            
            # Resume logic
            if state.get("last_processed_date"):
                last_dt = datetime.strptime(state["last_processed_date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
                start_dt = last_dt + timedelta(days=1)
                
                # [GUARDRAIL] Prevent future resume cursor
                now_dt = datetime.now(timezone.utc)
                if start_dt.date() > now_dt.date():
                    logger.warning(f"[GUARDRAIL] Future cursor detected: {start_dt.strftime('%Y-%m-%d')}. Real time: {now_dt.strftime('%Y-%m-%d')}.")
                    # Sanitize: reset to current real time
                    start_dt = now_dt.replace(hour=0, minute=0, second=0, microsecond=0)
                    logger.info(f"[GUARDRAIL] Cursor sanitized to real time: {start_dt.strftime('%Y-%m-%d')}")
                    # Clear stale future alerts that were causing persistent DEGRADED status
                    old_alerts = state.get("active_alerts", [])
                    state["active_alerts"] = [a for a in old_alerts if "failed at 2026-04" not in a]
                    if len(state["active_alerts"]) < len(old_alerts):
                        logger.info("[GUARDRAIL] Stale future alerts cleared from state.")
                
                logger.info(f"Resuming from last processed date: {state['last_processed_date']}. Next: {start_dt.strftime('%Y-%m-%d')}")
            elif start_date_str:
                start_dt = datetime.strptime(start_date_str, "%Y-%m-%d")
                logger.info(f"No previous state found. Starting fresh from: {start_date_str}")
            else:
                logger.error("No previous state found and no --start date provided.")
                return

            end_dt = start_dt + timedelta(days=days-1)
            
            # Convert back to strings for the pipeline CLI
            start_str = start_dt.strftime("%Y-%m-%d")
            end_str = end_dt.strftime("%Y-%m-%d")
            batch_id = f"batch_{start_dt.strftime('%Y%m%d')}_{end_dt.strftime('%Y%m%d')}"
            
            logger.info(f"Target Window: {start_str} to {end_str}")
            
            # Executing the script with absolute path
            script_path = self.root_dir / "scripts" / "run_shadow_pipeline.py"
            cmd = [
                sys.executable,
                str(script_path),
                "--start-date", start_str,
                "--end-date", end_str,
                "--append"
            ]
            
            logger.info(f"Executing: {' '.join(cmd)}")
            result = subprocess.run(cmd, cwd=str(self.root_dir), env={**os.environ, "PYTHONPATH": str(self.root_dir)})
            
            if result.returncode == 0:
                state["last_processed_date"] = end_str
                # Update status based on window success
                state["system_status"] = "HEALTHY" 
                state["active_alerts"] = []  # Clear previous alerts on success
                logger.info(f"Window {start_str} to {end_str} completed successfully.")
                
                # Update HITL Inbox
                try:
                    batch_path = self.obs_dir / "batches" / f"batch_report__{batch_id}.json"
                    hitl = HITLManager(self.obs_dir)
                    hitl.evaluate_batch(str(batch_path))
                except Exception as e:
                    logger.error(f"Failed to update HITL Inbox: {e}")

                self.save_state(state)
            else:
                state["system_status"] = "DEGRADED"
                state["active_alerts"] = [f"Pipeline failed at {end_str} with code {result.returncode}"]
                self.save_state(state)
                logger.error(f"Pipeline failed with return code {result.returncode}")

        finally:
            self._release_lock()

if __name__ == "__main__":
    import argparse
    from verticals.bitnin.services.bitnin_hitl.hitl_manager import HITLManager
    parser = argparse.ArgumentParser(description="BitNin Shadow Supervisor")
    parser.add_argument("--start", type=str, help="Start date if no state exists")
    parser.add_argument("--days", type=int, default=1, help="Number of days to process")
    args = parser.parse_args()
    
    # Accurate repo root detection: verticals/bitnin/services/bitnin_observability/supervisor.py
    current_file = Path(__file__).resolve()
    # Path is: /home/lucy-ubuntu/Escritorio/NIN/verticals/bitnin/services/bitnin_observability/supervisor.py
    # parents[0]: bitnin_observability/
    # parents[1]: services/
    # parents[2]: bitnin/
    # parents[3]: verticals/
    # parents[4]: NIN/
    REPO_ROOT = current_file.parents[4]
    
    supervisor = BitNinSupervisor(REPO_ROOT)
    supervisor.run_sustained(args.start, args.days)
