#!/usr/bin/env python3
import argparse
import sys
import json
from datetime import datetime, timezone
from pathlib import Path
from hitl_manager import HITLManager

def main():
    parser = argparse.ArgumentParser(description="BitNin HITL Operator Console")
    parser.add_argument("--obs-dir", default="verticals/bitnin/runtime/observability/", help="Path to observability directory")
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # list
    list_parser = subparsers.add_parser("list", help="List cases")
    list_parser.add_argument("--status", choices=["PENDING", "REVIEWED", "DISMISSED", "ESCALATED", "ALL"], default="PENDING")
    list_parser.add_argument("--limit", type=int, default=10)

    # show
    show_parser = subparsers.add_parser("show", help="Show case details and timeline")
    show_parser.add_argument("run_id", help="Run ID of the case")

    # review
    review_parser = subparsers.add_parser("review", help="Mark case as REVIEWED")
    review_parser.add_argument("run_id")
    review_parser.add_argument("--note", required=True, help="Operator notes")

    # dismiss
    dismiss_parser = subparsers.add_parser("dismiss", help="Mark case as DISMISSED")
    dismiss_parser.add_argument("run_id")
    dismiss_parser.add_argument("--note", required=True, help="Operator notes")

    # escalate
    escalate_parser = subparsers.add_parser("escalate", help="Mark case as ESCALATED")
    escalate_parser.add_argument("run_id")
    escalate_parser.add_argument("--note", required=True, help="Operator notes")

    # reopen
    reopen_parser = subparsers.add_parser("reopen", help="Mark case as PENDING again")
    reopen_parser.add_argument("run_id")
    reopen_parser.add_argument("--note", required=True, help="Operator notes")

    # rebuild
    subparsers.add_parser("rebuild", help="Force rebuild Markdown views")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    manager = HITLManager(args.obs_dir)
    state = manager.load_state()

    if args.command == "list":
        cases = state["cases"]
        if args.status != "ALL":
            cases = [c for c in cases if c["status"] == args.status]
        
        print(f"\n--- BitNin HITL Status: {args.status} (Total: {len(cases)}) ---")
        print(f"{'Run ID':<25} | {'Date':<12} | {'Priority':<10} | {'Status':<10}")
        print("-" * 65)
        for c in cases[:args.limit]:
            print(f"{c['run_id']:<25} | {c['date']:<12} | {c['priority']:<10} | {c['status']:<10}")
        if len(cases) > args.limit:
            print(f"... and {len(cases) - args.limit} more.")

    elif args.command == "show":
        case = next((c for c in state["cases"] if c["run_id"] == args.run_id), None)
        if not case:
            print(f"[ERROR] Case {args.run_id} not found.")
            return
        
        print(f"\n--- CASE FILE: {case['run_id']} ---")
        print(f"Date:     {case['date']}")
        print(f"Priority: {case['priority']}")
        print(f"Status:   {case['status']}")
        print(f"Reason:   {case['reason']}")
        print(f"Evidence: {case['evidence']['scorecard']}")
        print(f"Notes:    {case['operator_notes']}")
        print("\n--- TIMELINE ---")
        for entry in case["timeline"]:
            print(f"[{entry['timestamp']}] {entry['event'].upper()}: {entry['note']}")

    elif args.command in ["review", "dismiss", "escalate", "reopen"]:
        case = next((c for c in state["cases"] if c["run_id"] == args.run_id), None)
        if not case:
            print(f"[ERROR] Case {args.run_id} not found.")
            return
        
        old_status = case["status"]
        if args.command == "review": case["status"] = "REVIEWED"
        elif args.command == "dismiss": case["status"] = "DISMISSED"
        elif args.command == "escalate": case["status"] = "ESCALATED"
        elif args.command == "reopen": case["status"] = "PENDING"
        
        now = datetime.now(timezone.utc).isoformat()
        case["operator_notes"] = args.note
        case["last_updated"] = now
        case["timeline"].append({
            "event": args.command,
            "timestamp": now,
            "note": args.note
        })
        
        manager.save_state(state)
        manager.rebuild_views()
        print(f"[OK] Case {args.run_id} updated: {old_status} -> {case['status']}")

    elif args.command == "rebuild":
        manager.rebuild_views()
        print("[OK] Markdown views regenerated.")

if __name__ == "__main__":
    main()
