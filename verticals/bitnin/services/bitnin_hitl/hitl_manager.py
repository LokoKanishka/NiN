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
            self.state_file.write_text(json.dumps({
                "cases": [],
                "last_digest": None
            }, indent=2))
        
        self._write_md_headers()

    def _write_md_headers(self):
        # We only write if they don't exist or are empty
        header_inbox = "# BitNin — HITL Inbox (Active Cases)\n\n"
        header_inbox += "Casos pendientes de revisión o escalados.\n\n"
        header_inbox += "| Date | Case/Run ID | Priority | Reason | Status | Operator Notes | Evidence |\n"
        header_inbox += "|------|-------------|----------|--------|--------|----------------|----------|\n"
        
        header_archive = "# BitNin — HITL Archive (Closed Cases)\n\n"
        header_archive += "Casos revisados o descartados.\n\n"
        header_archive += "| Date | Case/Run ID | Priority | Reason | Status | Operator Notes | Evidence |\n"
        header_archive += "|------|-------------|----------|--------|--------|----------------|----------|\n"
        
        if not self.inbox_file.exists():
            self.inbox_file.write_text(header_inbox)
        if not self.archive_file.exists():
            self.archive_file.write_text(header_archive)

    def load_state(self):
        try:
            return json.loads(self.state_file.read_text())
        except Exception as e:
            logger.error(f"Failed to load state: {e}")
            return {"cases": []}

    def save_state(self, state):
        self.state_file.write_text(json.dumps(state, indent=2))

    def _sync_from_md(self, state):
        """Attempts to read statuses and notes from the inbox.md to update JSON state."""
        if not self.inbox_file.exists():
            return
            
        content = self.inbox_file.read_text()
        # More robust regex for table rows
        # Expects: | col1 | col2 | col3 | col4 | col5 | col6 | col7 |
        lines = content.splitlines()
        case_map = {c["run_id"]: c for c in state["cases"]}
        
        updated = False
        for line in lines:
            if "|" in line and "--|--" not in line and "Case/Run ID" not in line:
                parts = [p.strip() for p in line.split("|")]
                # [0] is empty (before first |), [1] is date, [2] is run_id, [3] is priority, [4] is reason, [5] is status, [6] is notes, [7] is link, [8] is empty
                if len(parts) >= 8:
                    run_id = parts[2]
                    status = parts[5].upper()
                    notes = parts[6]
                    
                    if run_id in case_map:
                        # Status Check
                        if status in ["PENDING", "REVIEWED", "DISMISSED", "ESCALATED"]:
                            if case_map[run_id]["status"] != status:
                                logger.info(f"Syncing status for {run_id}: {case_map[run_id]['status']} -> {status}")
                                case_map[run_id]["status"] = status
                                case_map[run_id]["last_updated"] = datetime.now(timezone.utc).isoformat()
                                updated = True
                        
                        # Notes Check
                        if notes != "-" and notes != case_map[run_id].get("operator_notes", "-"):
                            logger.info(f"Syncing notes for {run_id}")
                            case_map[run_id]["operator_notes"] = notes
                            case_map[run_id]["last_updated"] = datetime.now(timezone.utc).isoformat()
                            updated = True
        return updated

    def evaluate_batch(self, batch_report_path: str):
        logger.info(f"Evaluating batch for HITL: {batch_report_path}")
        try:
            with open(batch_report_path, "r") as f:
                batch = json.load(f)
        except Exception as e:
            logger.error(f"Failed to read batch report: {e}")
            return
        
        state = self.load_state()
        self._sync_from_md(state)
        
        batch_id = batch.get("batch_id", "Unknown")
        processed_run_ids = {c["run_id"] for c in state["cases"]}
        
        for run in batch.get("detailed_runs", []):
            run_id = run.get("run_id")
            if run_id in processed_run_ids:
                continue
            
            priority, reason = self._determine_priority(run)
            if priority != "LOW":
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
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "last_updated": datetime.now(timezone.utc).isoformat()
                }
                state["cases"].append(case)
        
        self.save_state(state)
        self._generate_views(state)
        self.generate_digest(batch, state)

    def _determine_priority(self, run):
        if run.get("composite_state") == "HIGH":
            return "🔴 HIGH", f"High Confidence Signal"
        if run.get("narrative_coverage", 1.0) < 0.1 and run.get("status") == "insufficient_evidence":
             return "🟡 MEDIUM", "Narrative Crash"
        if run.get("causal_typology") == "divergencia_critica":
            return "🔴 HIGH", "Critical Causal Divergence"
        if run.get("status") == "accepted_dry_run":
            return "🟢 LOW", "Healthy execution"
        return "LOW", "Routine"

    def _generate_views(self, state):
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

        header_inbox = "# BitNin — HITL Inbox (Active Cases)\n\nCasos pendientes de revisión o escalados.\n\n| Date | Case/Run ID | Priority | Reason | Status | Operator Notes | Evidence |\n|------|-------------|----------|--------|--------|----------------|----------|\n"
        self.inbox_file.write_text(header_inbox + "".join(inbox_rows))
        
        header_archive = "# BitNin — HITL Archive (Closed Cases)\n\nCasos revisados o descartados.\n\n| Date | Case/Run ID | Priority | Reason | Status | Operator Notes | Evidence |\n|------|-------------|----------|--------|--------|----------------|----------|\n"
        self.archive_file.write_text(header_archive + "".join(archive_rows))

    def generate_digest(self, last_batch, state):
        batch_id = last_batch.get("batch_id", "Unknown")
        stats = last_batch.get("health_summary", {})
        active_cases = [c for c in state["cases"] if c["status"] in ["PENDING", "ESCALATED"]]
        closed_cases = [c for c in state["cases"] if c["status"] in ["REVIEWED", "DISMISSED"]]
        
        md = f"# BitNin — Executive Digest (HITL)\n\n**Batch ID:** `{batch_id}` | **Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
        md += "## 📈 Backlog Status\n"
        md += f"- **Casos Abiertos**: {len(active_cases)} (Items en Inbox)\n"
        md += f"- **Casos Cerrados**: {len(closed_cases)} (Items en Archivo)\n\n"
        
        if active_cases:
            md += "### ⚠️ Casos Pendientes / Escalados\n"
            for c in active_cases[:5]:
                md += f"- **{c['priority']}** [{c['run_id']}](hitl_inbox.md): {c['reason']} ({c['date']})\n"
        
        md += "\n---\n*Referencia: [HITL Inbox](hitl_inbox.md) | [HITL Archive](hitl_archive.md)*"
        self.digest_file.write_text(md)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", required=False) # Optional for sync-only
    parser.add_argument("--obs-dir", required=True)
    parser.add_argument("--sync-only", action="store_true")
    args = parser.parse_args()
    
    manager = HITLManager(args.obs_dir)
    if args.sync_only:
        state = manager.load_state()
        if manager._sync_from_md(state):
            manager.save_state(state)
        manager._generate_views(state)
    else:
        manager.evaluate_batch(args.batch)
