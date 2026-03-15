from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ReportGenerator:
    """Generates human-readable and machine-readable reports from runtime artifacts."""

    def __init__(self, reports_dir: Path):
        self.reports_dir = reports_dir
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def generate_summary(self, mission_id: str, data: dict[str, Any]) -> Path:
        report_path = self.reports_dir / f"report_{mission_id}.md"
        
        md_content = f"# BitNin Mission Report: {mission_id}\n\n"
        md_content += f"Status: {data.get('status', 'N/A')}\n"
        md_content += f"Timestamp: {data.get('timestamp', 'N/A')}\n\n"
        
        md_content += "## Observability Results\n"
        for key, value in data.items():
            if key not in ["status", "timestamp"]:
                md_content += f"- **{key}**: {value}\n"
        
        report_path.write_text(md_content, encoding="utf-8")
        return report_path

    def write_json_report(self, mission_id: str, data: dict[str, Any]) -> Path:
        report_path = self.reports_dir / f"report_{mission_id}.json"
        report_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return report_path
