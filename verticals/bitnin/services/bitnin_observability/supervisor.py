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
        snapshot_path = self.obs_dir / "history" / "health_snapshot.md"
        logger.info(f"Generating health snapshot at: {snapshot_path}")
        
        # Freshness Check
        is_stale = False
        last_update_str = state.get("last_update")
        if last_update_str:
            last_update = datetime.fromisoformat(last_update_str)
            if datetime.now(timezone.utc) - last_update > timedelta(hours=25):
                is_stale = True
        
        md = f"# BitNin System Health Snapshot\n\n"
        md += f"**Last Update:** {last_update_str}\n"
        
        status = state.get('system_status', 'UNKNOWN')
        if is_stale:
            status = "STALE (Possible Freeze)"
            md += f"**System Status:** ⚠️ {status}\n"
        else:
            status_icon = "🟢" if status == "HEALTHY" else "🔴" if status == "DEGRADED" else "🟡"
            md += f"**System Status:** {status_icon} {status}\n"
            
        md += f"**Last Processed Date:** {state.get('last_processed_date', 'N/A')}\n"
        md += f"**Last Healthy Window:** {state.get('last_healthy_window', 'N/A')}\n\n"
        
        md += "## Active Alerts\n"
        alerts = state.get("active_alerts", [])
        if is_stale:
            md += f"- ⚠️ **STALE DATA**: System hasn't processed successfully in > 25 hours.\n"
        
        if not alerts and not is_stale:
            md += "- 🟢 All systems operational. No active alerts.\n"
        else:
            for alert in alerts:
                md += f"- {alert}\n"
        
        md += "\n---\n*This file is ephemeral and reflects current operational state.*"
        snapshot_path.write_text(md, encoding="utf-8")

    def run_sustained(self, start_date_str: str, days: int = 1):
        """Runs the pipeline for 'days' starting from start_date_str or the day after last_processed_date."""
        if not self._acquire_lock():
            return

        try:
            state = self.load_state()
            
            # Resume logic
            if state.get("last_processed_date"):
                last_dt = datetime.strptime(state["last_processed_date"], "%Y-%m-%d")
                start_dt = last_dt + timedelta(days=1)
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
