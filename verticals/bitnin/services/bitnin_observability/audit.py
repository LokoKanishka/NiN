from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import Any


class Auditor:
    """Manages audit logs for BitNin actions."""

    def __init__(self, audit_dir: Path):
        self.audit_dir = audit_dir
        self.audit_dir.mkdir(parents=True, exist_ok=True)

    def log(self, action: str, actor: str, details: dict[str, Any]):
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        entry = {
            "timestamp": timestamp,
            "action": action,
            "actor": actor,
            "details": details,
        }
        
        # Daily log file
        date_str = timestamp.split("T")[0]
        log_path = self.audit_dir / f"audit_{date_str}.jsonl"
        
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        
        return entry
