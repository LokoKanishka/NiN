import json
from pathlib import Path
from typing import Dict, Any, List, Tuple


class ScorecardGenerator:
    """Generates a markdown scorecard from a batch report and detects operational degradation."""

    def __init__(self, reports_dir: str):
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, batch_report_path: str) -> Tuple[Path, List[str]]:
        path = Path(batch_report_path)
        if not path.exists():
            raise FileNotFoundError(f"Batch report not found: {path}")

        data = json.loads(path.read_text(encoding="utf-8"))
        batch_id = data.get("batch_id", "unknown")
        total_runs = data.get("total_runs", 0)
        
        alerts = self._detect_degradation(data)
        md_content = self._build_markdown(data, alerts)
        
        scorecard_path = self.reports_dir / f"scorecard__{batch_id}.md"
        scorecard_path.write_text(md_content, encoding="utf-8")
        
        return scorecard_path, alerts

    def _detect_degradation(self, data: Dict[str, Any]) -> List[str]:
        alerts = []
        metrics = data.get("metrics_summary", {})
        total_runs = data.get("total_runs", 0)

        if total_runs == 0:
            alerts.append("🔴 **CRITICAL**: No runs executed in this batch.")
            return alerts

        # 1. Narrative collapse
        avg_narrative = metrics.get("average_narrative_coverage", 0.0)
        if avg_narrative < 0.2:
            alerts.append(f"🔴 **DEGRADATION**: Average narrative coverage critically low ({avg_narrative:.2f}). Is the dataset stuck?")

        # 2. Memory collapse
        runs_with_mem = metrics.get("runs_with_active_memory", 0)
        if total_runs >= 5 and runs_with_mem == 0:
            alerts.append("🔴 **DEGRADATION**: No active memory retrieved in any run. Vector index might be empty or disconnected.")

        # 3. State collapse
        states = metrics.get("composite_states", {})
        for state, count in states.items():
            if count == total_runs and total_runs >= 10:
                alerts.append(f"🟠 **WARNING**: 100% of runs collapsed into a single state ({state}). Check for lack of market variance.")

        if not alerts:
            alerts.append("🟢 **HEALTHY**: No degradation detected.")

        return alerts

    def _build_markdown(self, data: Dict[str, Any], alerts: List[str]) -> str:
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
        for alert in alerts:
            md += f"- {alert}\n"
        
        md += "\n## 1. Output Distribution\n"
        md += "| Final Status | Count | % |\n"
        md += "| :--- | :--- | :--- |\n"
        for st, count in statuses.items():
            pct = (count / total_runs * 100) if total_runs > 0 else 0
            md += f"| `{st}` | {count} | {pct:.1f}% |\n"
            
        md += "\n## 2. Composite Signal States\n"
        md += "| Convergence State | Count | % |\n"
        md += "| :--- | :--- | :--- |\n"
        for state, count in states.items():
            pct = (count / total_runs * 100) if total_runs > 0 else 0
            md += f"| `{state}` | {count} | {pct:.1f}% |\n"
            
        md += "\n## 3. Causal Typologies\n"
        md += "| Typology | Count | % |\n"
        md += "| :--- | :--- | :--- |\n"
        # Sort by count descending
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
        
        return md
