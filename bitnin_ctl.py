#!/usr/bin/env python3
import argparse
import sys
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from verticals.bitnin.services.bitnin_hitl.hitl_manager import HITLManager

# Configuration
OBS_DIR = Path("verticals/bitnin/runtime/observability/")
HEALTH_FILE = OBS_DIR / "history" / "health_snapshot.json"
BRIEFING_FILE = OBS_DIR / "history" / "hitl_briefing.md"

def get_scheduler_status():
    try:
        # Check timer
        timer_out = subprocess.check_output(["systemctl", "--user", "status", "bitnin.timer"], stderr=subprocess.STDOUT, text=True)
        is_active = "active (waiting)" in timer_out or "active (running)" in timer_out
        
        # Check next run
        list_timers = subprocess.check_output(["systemctl", "--user", "list-timers", "bitnin.timer"], text=True)
        # Parse next run date if possible
        next_run = "Unknown"
        lines = list_timers.splitlines()
        if len(lines) > 1:
            for line in lines:
                if "bitnin.timer" in line:
                    next_run = line.split()[0] + " " + line.split()[1]
        
        return {
            "is_timer_active": is_active,
            "next_run": next_run
        }
    except Exception as e:
        return {"error": f"Failed to get scheduler status: {e}"}

def color_status(status):
    if status == "HEALTHY": return f"\033[92m{status}\033[0m"
    if status == "DEGRADED": return f"\033[93m{status}\033[0m"
    if status == "STALE": return f"\033[91m{status}\033[0m"
    return status

def main():
    parser = argparse.ArgumentParser(description="BitNin Unified Command Console")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # status
    subparsers.add_parser("status", help="Unified system health and backlog status")
    
    # briefing
    subparsers.add_parser("briefing", help="Show daily operator briefing")

    # cases (sub-sub-commands)
    case_parser = subparsers.add_parser("cases", help="Manage HITL cases")
    case_subparsers = case_parser.add_subparsers(dest="case_command")
    
    list_p = case_subparsers.add_parser("list", help="List cases")
    list_p.add_argument("--status", choices=["PENDING", "REVIEWED", "DISMISSED", "ESCALATED", "ALL"], default="PENDING")
    
    show_p = case_subparsers.add_parser("show", help="Show case details")
    show_p.add_argument("case_id", help="Case ID (e.g., CASE-20260317-001)")
    
    review_p = case_subparsers.add_parser("review", help="Mark as REVIEWED")
    review_p.add_argument("case_id")
    review_p.add_argument("--note", required=True)
    
    dismiss_p = case_subparsers.add_parser("dismiss", help="Mark as DISMISSED")
    dismiss_p.add_argument("case_id")
    dismiss_p.add_argument("--note", required=True)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    manager = HITLManager(str(OBS_DIR))
    state = manager.load_state()

    if args.command == "status":
        print("\n=== 🎯 BITNIN STATUS 360° ===")
        # 1. Health
        if HEALTH_FILE.exists():
            health = json.loads(HEALTH_FILE.read_text())
            print(f"System Health: {color_status(health.get('status'))}")
            print(f"Timestamp:     {health.get('timestamp')}")
            print(f"Last Processed: {health.get('freshness', {}).get('last_run')}")
        else:
            print("System Health: UNKNOWN (health_snapshot.json missing)")

        # 2. Scheduler
        sched = get_scheduler_status()
        if "error" in sched:
            print(f"Scheduler:     \033[91mERROR\033[0m ({sched['error']})")
        else:
            icon = "🟢" if sched["is_timer_active"] else "🔴"
            print(f"Scheduler:     {icon} {'Active' if sched['is_timer_active'] else 'Inactive'}")
            print(f"Next Run:      {sched['next_run']}")

        # 3. Backlog
        cases = state.get("cases", [])
        pending = [c for c in cases if c["status"] == "PENDING"]
        escalated = [c for c in cases if c["status"] == "ESCALATED"]
        print(f"HITL Backlog:  {len(pending)} Pending, {len(escalated)} Escalated")
        print("==============================\n")

    elif args.command == "briefing":
        if BRIEFING_FILE.exists():
            print(BRIEFING_FILE.read_text())
        else:
            print("[ERROR] Briefing file not found. Run supervisor or hitl_manager first.")

    elif args.command == "cases":
        if not args.case_command:
            case_parser.print_help()
            return
            
        if args.case_command == "list":
            cases = state["cases"]
            if args.status != "ALL":
                cases = [c for c in cases if c["status"] == args.status]
            print(f"\n--- {args.status} CASES ({len(cases)}) ---")
            print(f"{'Case ID':<20} | {'Run ID':<25} | {'Priority':<10} | {'Status':<10}")
            print("-" * 75)
            for c in cases[:15]:
                print(f"{c['case_id']:<20} | {c['run_id']:<25} | {c['priority']:<10} | {c['status']:<10}")
        
        elif args.case_command == "show":
            case = next((c for c in state["cases"] if c["case_id"] == args.case_id or c["run_id"] == args.case_id), None)
            if not case:
                print(f"[ERROR] Case {args.case_id} not found.")
                return
            print(f"\n--- CASE FILE: {case['case_id']} ---")
            print(f"Run ID:   {case['run_id']}")
            print(f"Status:   {case['status']}")
            print(f"Priority: {case['priority']}")
            print(f"Reason:   {case['reason']}")
            print(f"Evidence: {case['evidence']['scorecard']}")
            print("\nTimeline:")
            for e in case["timeline"]:
                print(f" [{e['timestamp']}] {e['event'].upper()}: {e['note']}")

        elif args.case_command in ["review", "dismiss"]:
            case = next((c for c in state["cases"] if c["case_id"] == args.case_id), None)
            if not case:
                print(f"[ERROR] Case {args.case_id} not found.")
                return
            
            case["status"] = "REVIEWED" if args.case_command == "review" else "DISMISSED"
            now = datetime.now(timezone.utc).isoformat()
            case["operator_notes"] = args.note
            case["last_updated"] = now
            case["timeline"].append({
                "event": args.case_command,
                "timestamp": now,
                "note": args.note
            })
            manager.save_state(state)
            manager.rebuild_views()
            print(f"[OK] Case {case['case_id']} archived as {case['status']}.")

if __name__ == "__main__":
    main()
