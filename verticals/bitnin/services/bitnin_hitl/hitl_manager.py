import json
import os
import logging
import re
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger("bitnin_hitl")
logging.basicConfig(level=logging.INFO)

class HITLManager:
    def __init__(self, obs_dir: str):
        self.obs_dir = Path(obs_dir)
        self.history_dir = self.obs_dir / "history"
        self.inbox_file = self.history_dir / "hitl_inbox.md"
        self.archive_file = self.history_dir / "hitl_archive.md"
        self.state_file = self.history_dir / "hitl_state.json"
        self.digest_file = self.history_dir / "hitl_digest.md"
        
        self.history_dir.mkdir(parents=True, exist_ok=True)
        self._init_files()

    def _init_files(self):
        if not self.state_file.exists():
            self.save_state({
                "cases": [],
                "last_digest": None
            })
        self.rebuild_views()

    def load_state(self):
        try:
            state = json.loads(self.state_file.read_text())
            # Ensure all cases have a timeline (migration)
            for case in state.get("cases", []):
                if "timeline" not in case:
                    case["timeline"] = [{
                        "event": "migration_created",
                        "timestamp": case.get("created_at", datetime.now(timezone.utc).isoformat()),
                        "note": "Case migrated to Phase 22 structured format."
                    }]
            return state
        except Exception as e:
            logger.error(f"Failed to load state: {e}")
            return {"cases": []}

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
        batch_id = batch.get("batch_id", "Unknown")
        processed_run_ids = {c["run_id"] for c in state["cases"]}
        
        for run in batch.get("detailed_runs", []):
            run_id = run.get("run_id")
            if run_id in processed_run_ids:
                continue
            
            priority, reason = self._determine_priority(run)
            if priority != "LOW":
                now = datetime.now(timezone.utc).isoformat()
                case = {
                    "run_id": run_id,
                    "date": run.get("as_of", datetime.now().strftime("%Y-%m-%d")),
                    "priority": priority,
                    "reason": reason,
                    "status": "PENDING",
                    "operator_notes": "-",
                    "evidence": {
                        "batch_id": batch_id,
                        "scorecard": f"scorecards/scorecard__{batch_id}.md",
                        "composite_state": run.get("composite_state"),
                        "narrative_coverage": run.get("narrative_coverage")
                    },
                    "created_at": now,
                    "last_updated": now,
                    "timeline": [{
                        "event": "created",
                        "timestamp": now,
                        "note": f"System detected {priority} priority event. Reason: {reason}"
                    }]
                }
                state["cases"].append(case)
        
        self.save_state(state)
        self.rebuild_views()
        self.generate_digest(batch, state)

    def _determine_priority(self, run):
        if run.get("composite_state") == "HIGH":
            return "🔴 HIGH", f"High Confidence Signal"
        if run.get("narrative_coverage", 1.0) < 0.1 and run.get("status") == "insufficient_evidence":
             return "🟡 MEDIUM", "Narrative Crash"
        if run.get("causal_typology") == "divergencia_critica":
            return "🔴 HIGH", "Critical Causal Divergence"
            
        # Optional: other rules
        if run.get("status") == "accepted_dry_run":
            return "🟢 LOW", "Healthy execution"
        return "LOW", "Routine"

    def rebuild_views(self):
        """Regenerates hitl_inbox.md and hitl_archive.md from JSON state (Source of Truth)."""
        state = self.load_state()
        inbox_rows = []
        archive_rows = []
        sorted_cases = sorted(state["cases"], key=lambda x: x["date"], reverse=True)
        
        for c in sorted_cases:
            evidence_str = f"[Scorecard]({c['evidence']['scorecard']})"
            row = f"| {c['date']} | {c['run_id']} | {c['priority']} | {c['reason']} | {c['status']} | {c['operator_notes']} | {evidence_str} |\n"
            if c["status"] in ["PENDING", "ESCALATED"]:
                inbox_rows.append(row)
            else:
                archive_rows.append(row)

        warning_note = "> [!WARNING]\n> **NO EDITAR ESTE ARCHIVO MANUALMENTE.**\n> La sincronización desde Markdown ha sido deshabilitada en la Fase 22.\n> Use `python3 hitl_ctl.py` para gestionar los casos.\n\n"

        header_inbox = "# BitNin — HITL Inbox (Active Cases)\n\n" + warning_note + "Casos pendientes de revisión o escalados.\n\n| Date | Case/Run ID | Priority | Reason | Status | Operator Notes | Evidence |\n|------|-------------|----------|--------|--------|----------------|----------|\n"
        self.inbox_file.write_text(header_inbox + "".join(inbox_rows))
        
        header_archive = "# BitNin — HITL Archive (Closed Cases)\n\n" + warning_note + "Casos revisados o descartados.\n\n| Date | Case/Run ID | Priority | Reason | Status | Operator Notes | Evidence |\n|------|-------------|----------|--------|--------|----------------|----------|\n"
        self.archive_file.write_text(header_archive + "".join(archive_rows))
        logger.info("Markdown views rebuilt successfully.")

    def generate_digest(self, last_batch, state):
        batch_id = last_batch.get("batch_id", "Unknown")
        stats = last_batch.get("health_summary", {})
        active_cases = [c for c in state["cases"] if c["status"] in ["PENDING", "ESCALATED"]]
        closed_cases = [c for c in state["cases"] if c["status"] in ["REVIEWED", "DISMISSED"]]
        
        md = f"# BitNin — Executive Digest (HITL)\n\n"
        md += "> [!NOTE] Vista generada desde el estado estructurado.\n\n"
        md += f"**Batch ID:** `{batch_id}` | **Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
        md += "## 📈 Backlog Status\n"
        md += f"- **Casos Abiertos**: {len(active_cases)} (Items en Inbox/CLI)\n"
        md += f"- **Casos Cerrados**: {len(closed_cases)} (Items en Archivo)\n\n"
        
        if active_cases:
            md += "### ⚠️ Casos Pendientes / Escalados (Top 5)\n"
            for c in active_cases[:5]:
                md += f"- **{c['priority']}** [{c['run_id']}](hitl_inbox.md): {c['reason']} ({c['date']})\n"
        
        md += "\n---\n*Referencia: [HITL Inbox](hitl_inbox.md) | [HITL Archive](hitl_archive.md) | Use `hitl_ctl.py` para operar.*"
        self.digest_file.write_text(md)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", required=True)
    parser.add_argument("--obs-dir", required=True)
    args = parser.parse_args()
    
    manager = HITLManager(args.obs_dir)
    manager.evaluate_batch(args.batch)
