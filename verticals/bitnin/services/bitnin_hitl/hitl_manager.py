import json
import os
import logging
import re
import shutil
from datetime import datetime, timezone, timedelta
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
        self.briefing_file = self.history_dir / "hitl_briefing.md"
        self.journal_file = self.history_dir / "operator_journal.md"
        self.bundles_dir = self.history_dir / "daily_bundles"
        
        self.history_dir.mkdir(parents=True, exist_ok=True)
        self.bundles_dir.mkdir(parents=True, exist_ok=True)
        self._init_files()

    def _init_files(self):
        if not self.state_file.exists():
            self.save_state({
                "cases": [],
                "last_digest": None,
                "case_counter": 0
            })
        self.rebuild_views()

    def load_state(self):
        try:
            state = json.loads(self.state_file.read_text())
            if "case_counter" not in state:
                state["case_counter"] = len(state.get("cases", []))
            
            for case in state.get("cases", []):
                if "case_id" not in case:
                    state["case_counter"] += 1
                    case["case_id"] = f"CASE-{datetime.now().strftime('%Y%m%d')}-{state['case_counter']:03d}"
                
                if "timeline" not in case:
                    case["timeline"] = [{
                        "event": "migration_created",
                        "timestamp": case.get("created_at", datetime.now(timezone.utc).isoformat()),
                        "note": "Case migrated to Phase 23 structured format."
                    }]
            return state
        except Exception as e:
            logger.error(f"Failed to load state: {e}")
            return {"cases": [], "case_counter": 0}

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
                state["case_counter"] += 1
                case_id = f"CASE-{datetime.now().strftime('%Y%m%d')}-{state['case_counter']:03d}"
                
                case = {
                    "case_id": case_id,
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
                        "note": f"System detected {priority} priority event. Reason: {reason}. Run: {run_id}"
                    }]
                }
                state["cases"].append(case)
        
        self.save_state(state)
        self.rebuild_views()
        self.generate_digest(batch, state)
        self.generate_briefing(state)

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

    def rebuild_views(self):
        state = self.load_state()
        inbox_rows = []
        archive_rows = []
        sorted_cases = sorted(state["cases"], key=lambda x: x["date"], reverse=True)
        
        for c in sorted_cases:
            evidence_str = f"[Scorecard]({c['evidence']['scorecard']})"
            id_str = f"**{c['case_id']}**<br>({c['run_id']})"
            row = f"| {c['date']} | {id_str} | {c['priority']} | {c['reason']} | {c['status']} | {c['operator_notes']} | {evidence_str} |\n"
            if c["status"] in ["PENDING", "ESCALATED"]:
                inbox_rows.append(row)
            else:
                archive_rows.append(row)

        warning_note = "> [!IMPORTANT]\n> **VISTA DE SOLO LECTURA.**\n> Use `./bitnin_ctl.py cases` para gestionar estos expedientes.\n\n"

        header_inbox = "# BitNin — HITL Inbox (Active Cases)\n\n" + warning_note + "Casos pendientes de revisión o escalados.\n\n| Date | Case ID (Run) | Priority | Reason | Status | Operator Notes | Evidence |\n|------|---------------|----------|--------|--------|----------------|----------|\n"
        self.inbox_file.write_text(header_inbox + "".join(inbox_rows))
        
        header_archive = "# BitNin — HITL Archive (Closed Cases)\n\n" + warning_note + "Casos revisados o descartados.\n\n| Date | Case ID (Run) | Priority | Reason | Status | Operator Notes | Evidence |\n|------|---------------|----------|--------|--------|----------------|----------|\n"
        self.archive_file.write_text(header_archive + "".join(archive_rows))

    def generate_digest(self, last_batch, state):
        batch_id = last_batch.get("batch_id", "Unknown")
        active_cases = [c for c in state["cases"] if c["status"] in ["PENDING", "ESCALATED"]]
        closed_cases = [c for c in state["cases"] if c["status"] in ["REVIEWED", "DISMISSED"]]
        
        md = f"# BitNin — Executive Digest (HITL)\n\n"
        md += "> [!NOTE] Vista generada desde el estado estructurado.\n\n"
        md += f"**Batch ID:** `{batch_id}` | **Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
        md += "## 📈 Backlog Status\n"
        md += f"- **Casos Abiertos**: {len(active_cases)}\n"
        md += f"- **Casos Cerrados**: {len(closed_cases)}\n\n"
        
        if active_cases:
            md += "### ⚠️ Casos Críticos (Top 5)\n"
            for c in active_cases[:5]:
                md += f"- **{c['priority']}** {c['case_id']} ([Inbox](hitl_inbox.md)): {c['reason']} ({c['date']})\n"
        
        self.digest_file.write_text(md)

    def generate_briefing(self, state):
        now = datetime.now(timezone.utc)
        active_cases = [c for c in state["cases"] if c["status"] in ["PENDING", "ESCALATED"]]
        recent_closed = [c for c in state["cases"] if c["status"] in ["REVIEWED", "DISMISSED"] and (now - datetime.fromisoformat(c["last_updated"])).days < 1]
        
        md = f"# 📋 Briefing Diario del Operador — BitNin\n\n"
        md += f"*Generado: {now.strftime('%Y-%m-%d %H:%M:%S UTC')}*\n\n"
        
        md += "## 🛡️ Resumen de Operación\n"
        md += f"- **Casos Pendientes**: {len(active_cases)}\n"
        md += f"- **Casos Escalados**: {len([c for c in active_cases if c['status'] == 'ESCALATED'])}\n"
        md += f"- **Cierres en las últimas 24h**: {len(recent_closed)}\n\n"
        
        if active_cases:
            md += "## 🎯 Próximas Acciones Recomendadas\n"
            for c in active_cases[:3]:
                md += f"1. Revisar **{c['case_id']}** ({c['priority']}): {c['reason']}.\n"
        else:
            md += "✅ No hay casos pendientes de revisión inmediata.\n\n"
        
        md += "\n---\n*Referencia: use `./bitnin_ctl.py briefing` para ver el estado de salud completo.*"
        self.briefing_file.write_text(md)

    def close_day(self):
        """Generates the daily bundle and operator journal."""
        state = self.load_state()
        now = datetime.now(timezone.utc)
        today_str = now.strftime("%Y-%m-%d")
        
        # 1. Generate Journal of Human Decisions (Last 24h)
        journal_md = f"# 📔 Bitácora de Decisiones Humanas — {today_str}\n\n"
        cutoff = now - timedelta(hours=24)
        
        decisions = []
        for case in state["cases"]:
            for event in case["timeline"]:
                event_time = datetime.fromisoformat(event["timestamp"])
                if event_time > cutoff and event["event"] in ["review", "dismiss", "escalate", "reopen"]:
                    decisions.append({
                        "case_id": case["case_id"],
                        "event": event["event"].upper(),
                        "time": event["timestamp"],
                        "note": event["note"]
                    })
        
        if decisions:
            journal_md += "## 🏛️ Actividad del Día\n"
            for d in sorted(decisions, key=lambda x: x["time"]):
                journal_md += f"- **{d['case_id']}** ({d['event']}): {d['note']} *({d['time']})*\n"
        else:
            journal_md += "⚠️ No se registraron decisiones humanas en las últimas 24 horas.\n"
        
        journal_md += f"\n## 📊 Estado Final del Backlog\n"
        active = [c for c in state["cases"] if c["status"] in ["PENDING", "ESCALATED"]]
        journal_md += f"- **Pendientes**: {len(active)}\n"
        
        self.journal_file.write_text(journal_md)
        
        # 2. Create Daily Bundle Folder
        bundle_path = self.bundles_dir / today_str
        bundle_path.mkdir(parents=True, exist_ok=True)
        
        # Copy key artifacts to bundle
        shutil.copy2(self.briefing_file, bundle_path / "hitl_briefing.md")
        shutil.copy2(self.journal_file, bundle_path / "operator_journal.md")
        
        health_json = self.history_dir / "health_snapshot.json"
        if health_json.exists():
            shutil.copy2(health_json, bundle_path / "health_snapshot.json")
            
        logger.info(f"Daily bundle for {today_str} created successfully in {bundle_path}")
        return bundle_path

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", required=False)
    parser.add_argument("--obs-dir", required=True)
    parser.add_argument("--day-close", action="store_true")
    args = parser.parse_args()
    
    manager = HITLManager(args.obs_dir)
    if args.day_close:
        manager.close_day()
    elif args.batch:
        manager.evaluate_batch(args.batch)
