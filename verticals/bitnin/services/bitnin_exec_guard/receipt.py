"""
Receipt and persister for bitnin-exec-guard.
"""
import json
import os
from datetime import datetime, timezone
from typing import Dict, Any

RUNTIME_DIR = "/home/lucy-ubuntu/Escritorio/NIN/verticals/bitnin/runtime/execution"

class ReceiptManager:
    """Persists execution requests and results to local storage."""
    
    @staticmethod
    def persist_request(exec_id: str, payload: Dict[str, Any]) -> str:
        """Saves the request payload."""
        req_path = os.path.join(RUNTIME_DIR, "requests", f"{exec_id}_request.json")
        with open(req_path, "w") as f:
            json.dump(payload, f, indent=2)
        return req_path

    @staticmethod
    def persist_result(record: Dict[str, Any]) -> str:
        """Saves the execution record result."""
        exec_id = record["execution_id"]
        res_path = os.path.join(RUNTIME_DIR, "results", f"{exec_id}_record.json")
        with open(res_path, "w") as f:
            json.dump(record, f, indent=2)
        return res_path
        
    @staticmethod
    def log_event(exec_id: str, message: str):
        """Appends to a log file."""
        log_path = os.path.join(RUNTIME_DIR, "logs", f"{datetime.now(timezone.utc).date()}_exec.log")
        now_str = datetime.now(timezone.utc).isoformat()
        with open(log_path, "a") as f:
            f.write(f"[{now_str}] [{exec_id}] {message}\n")
