"""
CLI Builder/Runner for bitnin-exec-guard.
"""
import sys
import json
import argparse
from pathlib import Path
from typing import Any
from verticals.bitnin.services.bitnin_exec_guard.executor import ExecGuardExecutor
from verticals.bitnin.services.bitnin_exec_guard.receipt import ReceiptManager
from verticals.bitnin.services.bitnin_exec_guard.snapshot import SnapshotManager

class BitNinExecGuardRunner:
    def __init__(
        self,
        results_root: Path | str | None = None,
        snapshots_root: Path | str | None = None,
        logs_root: Path | str | None = None,
    ) -> None:
        self.results_root = Path(results_root) if results_root else None
        self.snapshots_root = Path(snapshots_root) if snapshots_root else None
        self.logs_root = Path(logs_root) if logs_root else None
        self.executor = ExecGuardExecutor()

    def run(self, *, intent_path: str, approval_path: str | None = None, analysis_path: str | None = None) -> dict[str, Any]:
        with open(intent_path, "r") as f:
            intent = json.load(f)
        
        approval = None
        if approval_path:
            with open(approval_path, "r") as f:
                approval = json.load(f)
        
        analysis = None
        if analysis_path:
            with open(analysis_path, "r") as f:
                analysis = json.load(f)
        
        record = self.executor.execute(intent=intent, approval=approval, analysis=analysis)
        exec_id = record["execution_id"]
        
        # Persistence (using ReceiptManager which defaults to runtime/execution paths if not overridden globally)
        payload = {"intent": intent, "approval": approval, "analysis": analysis}
        req_path = ReceiptManager.persist_request(exec_id, payload)
        res_path = ReceiptManager.persist_result(record)
        ReceiptManager.log_event(exec_id, f"Execution completed with status: {record['status']}")
        snap_path = SnapshotManager.create_snapshot(exec_id, req_path, res_path)
        
        return {
            "record": record,
            "record_path": str(res_path),
            "request_path": str(req_path),
            "snapshot_path": str(snap_path)
        }

def main():
    parser = argparse.ArgumentParser(description="BitNin Exec Guard Builder")
    parser.add_argument("--intent", required=True, help="Path to trade_intent JSON")
    parser.add_argument("--approval", required=False, help="Path to approval JSON")
    parser.add_argument("--analysis", required=False, help="Path to analysis JSON")
    
    args = parser.parse_args()
    
    with open(args.intent, "r") as f:
        intent = json.load(f)
        
    approval = None
    if args.approval:
        with open(args.approval, "r") as f:
            approval = json.load(f)
            
    analysis = None
    if args.analysis:
        with open(args.analysis, "r") as f:
            analysis = json.load(f)
            
    executor = ExecGuardExecutor()
    record = executor.execute(intent=intent, approval=approval, analysis=analysis)
    
    exec_id = record["execution_id"]
    
    # Save Request Payload
    payload = {
        "intent": intent,
        "approval": approval,
        "analysis": analysis
    }
    req_path = ReceiptManager.persist_request(exec_id, payload)
    
    # Save Result
    res_path = ReceiptManager.persist_result(record)
    
    # Log
    ReceiptManager.log_event(exec_id, f"Execution completed with status: {record['status']}")
    
    # Snapshot
    snap_path = SnapshotManager.create_snapshot(exec_id, req_path, res_path)
    
    print(json.dumps(record, indent=2))
    print(f"\nSnapshot created at: {snap_path}")

if __name__ == "__main__":
    main()
