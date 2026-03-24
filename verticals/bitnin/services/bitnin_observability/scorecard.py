import json
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional


class ScorecardGenerator:
    """Generates a markdown scorecard from a batch report and detects operational degradation and drift."""

    def __init__(self, reports_dir: str, history_path: Optional[str] = None):
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.history_path = Path(history_path) if history_path else None

    def generate(self, batch_report_path: str) -> Tuple[Path, List[str]]:
        path = Path(batch_report_path)
        if not path.exists():
            raise FileNotFoundError(f"Batch report not found: {path}")

        data = json.loads(path.read_text(encoding="utf-8"))
        batch_id = data.get("batch_id", "unknown")
        
        # Load history for drift detection if available
        history = self._load_history()
        
        alerts = self._detect_degradation(data)
        drift_alerts = self._detect_drift(data, history)
        combined_alerts = alerts + drift_alerts
        
        md_content = self._build_markdown(data, combined_alerts, history)
        
        scorecard_path = self.reports_dir / f"scorecard__{batch_id}.md"
        scorecard_path.write_text(md_content, encoding="utf-8")
        
        # Update history if configured
        self._update_history(data)
        
        return scorecard_path, combined_alerts

    def _load_history(self) -> List[Dict[str, Any]]:
        if not self.history_path or not self.history_path.exists():
            return []
        try:
            return json.loads(self.history_path.read_text(encoding="utf-8"))
        except Exception:
            return []

    def _update_history(self, current_batch: Dict[str, Any]) -> None:
        if not self.history_path:
            return
        
        history = self._load_history()
        # Clean current batch for history (only summary level)
        history_entry = {
            "batch_id": current_batch.get("batch_id"),
            "timestamp": current_batch.get("timestamp"),
            "total_runs": current_batch.get("total_runs"),
            "metrics_summary": current_batch.get("metrics_summary"),
            "statuses": current_batch.get("statuses"),
        }
        
        # Keep only last 10 batches for comparison
        history.append(history_entry)
        if len(history) > 10:
            history = history[-10:]
            
        self.history_path.write_text(json.dumps(history, indent=2), encoding="utf-8")

    def _detect_degradation(self, data: Dict[str, Any]) -> List[str]:
        alerts = []
        metrics = data.get("metrics_summary", {})
        total_runs = data.get("total_runs", 0)

        if total_runs == 0:
            alerts.append("🔴 **CRITICAL**: No runs executed in this batch.")
            return alerts

        # 1. Narrative collapse
        avg_narrative = metrics.get("average_narrative_coverage", 0.0)
        ingestion_fails = metrics.get("ingestion_failures", 0)
        
        if ingestion_fails > 0:
            alerts.append(f"🟠 **INGESTION**: {ingestion_fails} runs affected by GDELT fetch failures.")
        
        if avg_narrative < 0.2:
            alerts.append(f"🔴 **DEGRADATION**: Average narrative coverage critically low ({avg_narrative:.2f}).")

        # 2. Memory collapse
        runs_with_mem = metrics.get("runs_with_active_memory", 0)
        if total_runs >= 3 and runs_with_mem == 0:
            alerts.append("🔴 **DEGRADATION**: No active memory retrieved in any run.")

        # 3. State collapse
        states = metrics.get("composite_states", {})
        for state, count in states.items():
            if count == total_runs and total_runs >= 5:
                alerts.append(f"🟠 **WARNING**: 100% of runs collapsed into a single state ({state}).")

        return alerts

    def _detect_drift(self, current: Dict[str, Any], history: List[Dict[str, Any]]) -> List[str]:
        if not history:
            return []
        
        alerts = []
        prev = history[-1]
        
        curr_metrics = current.get("metrics_summary", {})
        prev_metrics = prev.get("metrics_summary", {})
        
        # 1. State Distribution Drift
        curr_states = current.get("statuses", {})
        prev_states = prev.get("statuses", {})
        
        # Example: if 'accepted' was predominant and now is zero
        if prev_states.get("accepted", 0) > 0 and curr_states.get("accepted", 0) == 0:
            alerts.append("🟡 **DRIFT**: Significant drop in 'accepted' status compared to previous window.")

        # 2. Narrative Drift
        curr_narr = curr_metrics.get("average_narrative_coverage", 0.0)
        prev_narr = prev_metrics.get("average_narrative_coverage", 0.0)
        if prev_narr > 0 and curr_narr < (prev_narr * 0.5):
             alerts.append(f"🟡 **DRIFT**: Narrative coverage dropped by >50% (from {prev_narr:.2f} to {curr_narr:.2f}).")

        return alerts

    def _build_markdown(self, data: Dict[str, Any], alerts: List[str], history: List[Dict[str, Any]]) -> str:
        batch_id = data.get("batch_id", "unknown")
        total_runs = data.get("total_runs", 0)
        metrics = data.get("metrics_summary", {})
        statuses = data.get("statuses", {})
        states = metrics.get("composite_states", {})
        typologies = metrics.get("causal_typologies", {})
        
        md = f"# BitNin Longitudinal Scorecard: {batch_id}\n\n"
        md += f"**Timestamp:** {data.get('timestamp')}\n"
        md += f"**Total Runs:** {total_runs}\n\n"
        
        md += "## Configuration & Health Alerts\n"
        if not [a for a in alerts if "🔴" in a or "🟠" in a or "🟡" in a]:
            md += "- 🟢 **HEALTHY**: No degradation or drift detected.\n"
        else:
            for alert in alerts:
                md += f"- {alert}\n"
        
        md += "\n## 1. Output Distribution\n"
        md += "| Final Status | Count | Current % | Previous % |\n"
        md += "| :--- | :--- | :--- | :--- |\n"
        
        prev_statuses = history[-1].get("statuses", {}) if history else {}
        prev_total = history[-1].get("total_runs", 0) if history else 0
        
        all_status_keys = sorted(set(list(statuses.keys()) + list(prev_statuses.keys())))
        for st in all_status_keys:
            count = statuses.get(st, 0)
            pct = (count / total_runs * 100) if total_runs > 0 else 0
            prev_pct = (prev_statuses.get(st, 0) / prev_total * 100) if prev_total > 0 else 0
            md += f"| `{st}` | {count} | {pct:.1f}% | {prev_pct:.1f}% |\n"
            
        md += "\n## 2. Composite Signal States\n"
        md += "| Convergence State | Count | % |\n"
        md += "| :--- | :--- | :--- |\n"
        for state, count in states.items():
            pct = (count / total_runs * 100) if total_runs > 0 else 0
            md += f"| `{state}` | {count} | {pct:.1f}% |\n"
            
        md += "\n## 3. Causal Typologies\n"
        md += "| Typology | Count | % |\n"
        md += "| :--- | :--- | :--- |\n"
        sorted_typ = sorted(typologies.items(), key=lambda x: x[1], reverse=True)
        for typ, count in sorted_typ:
            pct = (count / total_runs * 100) if total_runs > 0 else 0
            md += f"| `{typ}` | {count} | {pct:.1f}% |\n"
            
        md += "\n## 4. Operational Coverages\n"
        avg_narr = metrics.get("average_narrative_coverage", 0.0)
        runs_mem = metrics.get("runs_with_active_memory", 0)
        mem_pct = (runs_mem / total_runs * 100) if total_runs > 0 else 0
        
        md += f"- **Average Narrative Coverage:** `{avg_narr:.2f}`\n"
        md += f"- **Runs with Active Memory:** `{runs_mem}` (`{mem_pct:.1f}%`)\n"
        md += f"- **GDELT Ingestion Failures:** `{metrics.get('ingestion_failures', 0)}`\n"
        
        if history:
            md += "\n## 5. Temporal Trends (Last Batches)\n"
            md += "| Batch ID | Narrative Cover | Memory % | Dominant State |\n"
            md += "| :--- | :--- | :--- | :--- |\n"
            for entry in history[-5:]:
                entry_metrics = entry.get("metrics_summary", {})
                entry_narr = entry_metrics.get("average_narrative_coverage", 0.0)
                entry_mem_runs = entry_metrics.get("runs_with_active_memory", 0)
                entry_total = entry.get("total_runs", 1)
                entry_mem_pct = (entry_mem_runs / entry_total * 100)
                
                entry_states = entry_metrics.get("composite_states", {})
                dom_state = max(entry_states.items(), key=lambda x: x[1])[0] if entry_states else "N/A"
                
                md += f"| `{entry['batch_id']}` | {entry_narr:.2f} | {entry_mem_pct:.1f}% | `{dom_state}` |\n"
                
        return md
