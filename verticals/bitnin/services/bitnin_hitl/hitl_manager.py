import json
import os
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger("bitnin_hitl")
logging.basicConfig(level=logging.INFO)

class HITLManager:
    def __init__(self, obs_dir: str):
        self.obs_dir = Path(obs_dir)
        self.history_dir = self.obs_dir / "history"
        self.inbox_file = self.history_dir / "hitl_inbox.md"
        self.state_file = self.history_dir / "hitl_state.json"
        self.digest_file = self.history_dir / "hitl_digest.md"
        
        self.history_dir.mkdir(parents=True, exist_ok=True)
        self._init_files()

    def _init_files(self):
        if not self.inbox_file.exists():
            header = "# BitNin — HITL Inbox (Bandeja de Revisión)\n\n"
            header += "Este buzón captura eventos que requieren juicio humano. Una vez revisados, un operador puede marcar el estado como `REVIEWED` o `DISMISSED` en este archivo.\n\n"
            header += "| Date | Run ID | Priority | Reason | Status | Decision/Note | Link |\n"
            header += "|------|--------|----------|--------|--------|---------------|------|\n"
            self.inbox_file.write_text(header)
        
        if not self.state_file.exists():
            self.state_file.write_text(json.dumps({
                "processed_runs": [],
                "decisions": {}, # run_id -> {status, note, timestamp}
                "last_digest": None
            }))

    def load_state(self):
        try:
            return json.loads(self.state_file.read_text())
        except:
            return {"processed_runs": [], "decisions": {}, "last_digest": None}

    def save_state(self, state):
        self.state_file.write_text(json.dumps(state, indent=2))

    def evaluate_batch(self, batch_report_path: str):
        logger.info(f"Evaluating batch for HITL: {batch_report_path}")
        try:
            with open(batch_report_path, "r") as f:
                batch = json.load(f)
        except Exception as e:
            logger.error(f"Failed to read batch report: {e}")
            return
        
        state = self.load_state()
        new_entries = []
        
        # Deduplication logic: grouping similar consecutive events
        # For now, we focus on identifying new unique runs
        for run in batch.get("detailed_runs", []):
            run_id = run.get("run_id")
            if run_id in state["processed_runs"]:
                continue
            
            priority, reason = self._determine_priority(run)
            
            # Grouping/Deduplication check: 
            # If priority and reason are same as last processed run, we might tag it
            # But for the inbox, we want individual traceability.
            
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
        
        # Refresh decision states from the markdown file if possible (bi-directional sync attempt)
        # However, for simplicity now, we trust the state for generation.
        
        # Cleanup state
        if len(state["processed_runs"]) > 2000:
            state["processed_runs"] = state["processed_runs"][-2000:]
            
        self.save_state(state)
        self.generate_digest(batch)

    def _determine_priority(self, run):
        if run.get("composite_state") == "HIGH":
            return "🔴 HIGH", f"High Confidence ({run.get('status')})"
        
        if run.get("narrative_coverage", 1.0) < 0.1 and run.get("status") == "insufficient_evidence":
             return "🟡 MEDIUM", "Narrative Crash"
             
        if run.get("causal_typology") == "divergencia_critica":
            return "🔴 HIGH", "Critical Causal Divergence"
            
        if run.get("status") == "accepted_dry_run":
            return "🟢 LOW", "Healthy execution"

        return "LOW", "Routine"

    def _update_inbox(self, entries):
        with open(self.inbox_file, "a") as f:
            for e in entries:
                # Link format: [Scorecard](scorecards/scorecard__batch_...)
                # Simplifying link for now
                line = f"| {e['date']} | {e['run_id']} | {e['priority']} | {e['reason']} | {e['status']} | - | [Scorecard](scorecards/) |\n"
                f.write(line)

    def generate_digest(self, last_batch):
        """Generates a compact executive summary."""
        logger.info("Generating HITL Digest")
        
        batch_id = last_batch.get("batch_id", "Unknown")
        stats = last_batch.get("health_summary", {})
        o_stats = last_batch.get("outcomes", {})
        m_stats = last_batch.get("metrics_summary", {})
        
        md = f"# BitNin — Executive Digest (HITL)\n\n"
        md += f"**Batch ID:** `{batch_id}` | **Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
        
        md += "## 📊 Operational Health\n"
        md += f"- **Outcome**: {o_stats}\n"
        md += f"- **Narrative Coverage (Avg)**: {m_stats.get('average_narrative_coverage', 0):.2f}\n"
        md += f"- **Composite States**: {m_stats.get('composite_states', {})}\n\n"
        
        md += "## 🎯 Critical Items for Review\n"
        critical_runs = [r for r in last_batch.get("detailed_runs", []) if self._determine_priority(r)[0] == "🔴 HIGH"]
        
        if critical_runs:
            for r in critical_runs:
                md += f"- 🔴 **{r['run_id']}**: {self._determine_priority(r)[1]} (as_of: {r.get('as_of')})\n"
        else:
            md += "- ✅ No high-priority items in this batch.\n\n"
        
        md += "## 🛡️ Infrastructure Status\n"
        for svc, s in stats.items():
            icon = "🟢" if s.get("UP", 0) > 0 else "🔴"
            md += f"- {icon} **{svc.upper()}**: {s}\n"
            
        md += "\n---\n*Para más detalles, revise el [HITL Inbox](hitl_inbox.md) o los scorecards individuales.*"
        self.digest_file.write_text(md)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", required=True)
    parser.add_argument("--obs-dir", required=True)
    args = parser.parse_args()
    
    manager = HITLManager(args.obs_dir)
    manager.evaluate_batch(args.batch)
