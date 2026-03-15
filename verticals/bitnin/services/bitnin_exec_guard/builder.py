"""
CLI Builder/Runner for bitnin-exec-guard.
"""
import sys
import json
import argparse
from verticals.bitnin.services.bitnin_exec_guard.executor import ExecGuardExecutor
from verticals.bitnin.services.bitnin_exec_guard.receipt import ReceiptManager
from verticals.bitnin.services.bitnin_exec_guard.snapshot import SnapshotManager

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
