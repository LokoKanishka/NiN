import json
import os
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("bitnin_hitl")
logging.basicConfig(level=logging.INFO)

class HITLManager:
    def __init__(self, obs_dir: str):
        self.obs_dir = Path(obs_dir)
        self.history_dir = self.obs_dir / "history"
        self.inbox_file = self.history_dir / "hitl_inbox.md"
        self.state_file = self.history_dir / "hitl_state.json"
        
        self.history_dir.mkdir(parents=True, exist_ok=True)
        self._init_inbox()

    def _init_inbox(self):
        if not self.inbox_file.exists():
            header = "# BitNin — HITL Inbox (Bandeja de Revisión)\n\n"
            header += "| Date | Run ID | Priority | Reason | Status | Link |\n"
            header += "|------|--------|----------|--------|--------|------|\n"
            self.inbox_file.write_text(header)
        
        if not self.state_file.exists():
            self.state_file.write_text(json.dumps({"processed_runs": []}))

    def load_state(self):
        try:
            return json.loads(self.state_file.read_text())
        except:
            return {"processed_runs": []}

    def save_state(self, state):
        self.state_file.write_text(json.dumps(state, indent=2))

    def evaluate_batch(self, batch_report_path: str):
        logger.info(f"Evaluating batch for HITL: {batch_report_path}")
        with open(batch_report_path, "r") as f:
            batch = json.load(f)
        
        state = self.load_state()
        new_entries = []
        
        for run in batch.get("detailed_runs", []):
            run_id = run.get("run_id")
            if run_id in state["processed_runs"]:
                continue
            
            priority, reason = self._determine_priority(run)
            if priority != "LOW":
                entry = {
                    "date": run.get("as_of", datetime.now().strftime("%Y-%m-%d")),
                    "run_id": run_id,
                    "priority": priority,
                    "reason": reason,
                    "status": "PENDING"
                }
                new_entries.append(entry)
            
            state["processed_runs"].append(run_id)
        
        if new_entries:
            self._update_inbox(new_entries)
        
        # Keep state size manageable
        if len(state["processed_runs"]) > 1000:
            state["processed_runs"] = state["processed_runs"][-1000:]
            
        self.save_state(state)

    def _determine_priority(self, run):
        # Logic for selection
        if run.get("composite_state") == "HIGH":
            return "🔴 HIGH", "High Confidence Signal detected"
        
        if run.get("narrative_coverage", 1.0) < 0.1 and run.get("status") == "insufficient_evidence":
             return "🟡 MEDIUM", "Narrative Crash (Possible data gap)"
             
        if run.get("causal_typology") == "divergencia_critica":
            return "🔴 HIGH", "Critical Causal Divergence"
            
        if run.get("status") == "accepted_dry_run":
            return "🟢 LOW", "Healthy execution"

        return "LOW", "Routine"

    def _update_inbox(self, entries):
        with open(self.inbox_file, "a") as f:
            for e in entries:
                # Map run_id to scorecard path (convention)
                # scorecard__batch_20260325_20260325.md
                # This logic might need refinement if batches contain many runs
                line = f"| {e['date']} | {e['run_id']} | {e['priority']} | {e['reason']} | {e['status']} | [Scorecard](scorecards/) |\n"
                f.write(line)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", required=True)
    parser.add_argument("--obs-dir", required=True)
    args = parser.parse_args()
    
    manager = HITLManager(args.obs_dir)
    manager.evaluate_batch(args.batch)
