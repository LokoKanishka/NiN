#!/usr/bin/env python3
import argparse
import sys
import json
import subprocess
import os
from datetime import datetime, timezone
from pathlib import Path

# --- Entrypoint & Path Logic ---
# Find project root (where bitnin_ctl.py lives)
ROOT_DIR = Path(__file__).parent.resolve()
sys.path.append(str(ROOT_DIR))

# Import logic from verticals (with absolute imports from root)
try:
    from verticals.bitnin.services.bitnin_hitl.hitl_manager import HITLManager
except ImportError:
    print("[CRITICAL] Could not import HITLManager. Ensure you are running from project root.")
    sys.exit(1)

# Configuration
OBS_DIR = ROOT_DIR / "verticals/bitnin/runtime/observability"
HISTORY_DIR = OBS_DIR / "history"
HEALTH_FILE = HISTORY_DIR / "health_snapshot.json"
BRIEFING_FILE = HISTORY_DIR / "hitl_briefing.md"
JOURNAL_FILE = HISTORY_DIR / "operator_journal.md"
STATE_FILE = HISTORY_DIR / "hitl_state.json"

def get_scheduler_status():
    try:
        # Check timer
        timer_out = subprocess.check_output(["systemctl", "--user", "status", "bitnin-shadow.timer"], stderr=subprocess.STDOUT, text=True)
        is_active = "active (waiting)" in timer_out or "active (running)" in timer_out
        
        # Check next run
        list_timers = subprocess.check_output(["systemctl", "--user", "list-timers", "bitnin-shadow.timer"], text=True)
        next_run = "Unknown"
        lines = list_timers.splitlines()
        if len(lines) > 1:
            for line in lines:
                if "bitnin-shadow.timer" in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        next_run = f"{parts[0]} {parts[1]}"
        
        return {
            "is_timer_active": is_active,
            "next_run": next_run
        }
    except Exception as e:
        return {"error": str(e)}

def color_status(status):
    if status == "HEALTHY": return f"\033[92m{status}\033[0m"
    if status == "DEGRADED": return f"\033[93m{status}\033[0m"
    if status == "STALE": return f"\033[91m{status}\033[0m"
    return status

def run_doctor():
    print("\n=== 🧑‍⚕️ BITNIN DOCTOR (Diagnostic Report) ===")
    
    def check(label, condition, fix=None):
        status = "✅ OK" if condition else "❌ FAIL"
        color = "\033[92m" if condition else "\033[91m"
        print(f"[{color}{status}\033[0m] {label}")
        if not condition and fix:
            print(f"      💡 Fix: {fix}")

    # 1. Paths & Files
    check("Project Root Access", ROOT_DIR.exists())
    check("Runtime Directory Structure", OBS_DIR.exists(), "run ./scripts/bootstrap.sh")
    check("HITL State File present", STATE_FILE.exists(), "system will auto-create on first batch")
    
    # 2. Permissions
    check("bitnin_ctl.py executable", os.access(ROOT_DIR / "bitnin_ctl.py", os.X_OK), "chmod +x bitnin_ctl.py")
    check("bin/bitnin-ctl wrapper present", (ROOT_DIR / "bin/bitnin-ctl").exists(), "run ./scripts/bootstrap.sh")

    # 3. Environment
    check("PYTHONPATH set (internal)", str(ROOT_DIR) in sys.path)
    
    # 4. Infrastructure
    sched = get_scheduler_status()
    check("Systemd --user accessible", "error" not in sched, "ensure 'systemd --user' is supported/active")
    if "error" not in sched:
        check("BitNin Timer Active", sched["is_timer_active"], "./scripts/scheduler_ctl.sh install")
    
    # 5. User Linger
    try:
        user = os.environ.get("USER", "unknown")
        linger_out = subprocess.check_output(["loginctl", "show-user", user], text=True)
        is_linger = "Linger=yes" in linger_out
        check(f"User Linger Enabled ({user})", is_linger, f"loginctl enable-linger {user}")
    except:
        print("[⚠️] Could not verify Linger status.")

    print("==========================================\n")

def main():
    parser = argparse.ArgumentParser(description="BitNin Unified Command Console (Mando Maestro)")
    subparsers = parser.add_subparsers(dest="command", help="Comandos Principales")

    # status
    subparsers.add_parser("status", help="Vista 360° de salud y backlog")
    
    # briefing
    subparsers.add_parser("briefing", help="Resumen ejecutivo diario")

    # day-close
    subparsers.add_parser("day-close", help="Ejecutar ritual de cierre de jornada y bitácora")

    # doctor
    subparsers.add_parser("doctor", help="Diagnóstico técnico de la instalación")

    # cases
    case_parser = subparsers.add_parser("cases", help="Gestión de expedientes HITL")
    case_subparsers = case_parser.add_subparsers(dest="case_command")
    
    list_p = case_subparsers.add_parser("list", help="Listado de casos")
    list_p.add_argument("--status", choices=["PENDING", "REVIEWED", "DISMISSED", "ESCALATED", "ALL"], default="PENDING")
    
    show_p = case_subparsers.add_parser("show", help="Inspección de un caso")
    show_p.add_argument("case_id", help="Case ID (e.g., CASE-20260317-001)")
    
    review_p = case_subparsers.add_parser("review", help="Marcar como REVIEWED")
    review_p.add_argument("case_id")
    review_p.add_argument("--note", required=True)
    
    dismiss_p = case_subparsers.add_parser("dismiss", help="Marcar como DISMISSED")
    dismiss_p.add_argument("case_id")
    dismiss_p.add_argument("--note", required=True)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    manager = HITLManager(str(OBS_DIR))
    state = manager.load_state()

    if args.command == "doctor":
        run_doctor()
        return

    if args.command == "status":
        print("\n=== 🎯 BITNIN STATUS 360° ===")
        # 1. Health
        if HEALTH_FILE.exists():
            health = json.loads(HEALTH_FILE.read_text())
            print(f"System Health: {color_status(health.get('status'))}")
            print(f"Timestamp:     {health.get('timestamp')}")
            print(f"Last Processed: {health.get('freshness', {}).get('last_run')}")
        else:
            print("System Health: \033[91mUNKNOWN\033[0m (Snapshot faltante)")

        # 2. Scheduler
        sched = get_scheduler_status()
        if "error" in sched:
            print(f"Scheduler:     \033[93mDEGRADED\033[0m (systemd inaccessible o sin configurar)")
        else:
            icon = "🟢" if sched["is_timer_active"] else "🔴"
            print(f"Scheduler:     {icon} {'Active' if sched['is_timer_active'] else 'Inactive'}")
            print(f"Next Run:      {sched['next_run']}")

        # 3. Backlog
        cases = state.get("cases", [])
        pending = [c for c in cases if c["status"] == "PENDING"]
        escalated = [c for c in cases if c["status"] == "ESCALATED"]
        print(f"HITL Backlog:  \033[96m{len(pending)} Pendientes\033[0m, {len(escalated)} Escalados")
        print("==============================\n")

    elif args.command == "briefing":
        if BRIEFING_FILE.exists():
            print(BRIEFING_FILE.read_text())
        else:
            print("[ERROR] Briefing no generado aún.")

    elif args.command == "day-close":
        print("\n--- 🏁 RITUAL DE CIERRE DE JORNADA ---")
        bundle_path = manager.close_day()
        print(f"[OK] Bundle diario generado en: \n     {bundle_path.relative_to(ROOT_DIR)}")
        
        if JOURNAL_FILE.exists():
            print("\n--- BITÁCORA DE ACTIVIDAD ---")
            print(JOURNAL_FILE.read_text())
        print("Cierre de jornada completado con éxito.\n")

    elif args.command == "cases":
        if not args.case_command:
            case_parser.print_help()
            return
            
        if args.case_command == "list":
            cases = state["cases"]
            if args.status != "ALL":
                cases = [c for c in cases if c["status"] == args.status]
            print(f"\n--- {args.status} CASES ({len(cases)}) ---")
            print(f"{'Case ID':<20} | {'Priority':<10} | {'Status':<10} | {'Updated':<20}")
            print("-" * 75)
            for c in sorted(cases, key=lambda x: x["last_updated"], reverse=True)[:15]:
                print(f"{c['case_id']:<20} | {c['priority']:<10} | {c['status']:<10} | {c['last_updated'][:19]}")
        
        elif args.case_command == "show":
            case = next((c for c in state["cases"] if c["case_id"] == args.case_id or c["run_id"] == args.case_id), None)
            if not case:
                print(f"[ERROR] Caso {args.case_id} no encontrado.")
                return
            print(f"\n--- CASE FILE: {case['case_id']} ---")
            print(f"Run ID:   {case['run_id']}")
            print(f"Status:   {case['status']}")
            print(f"Priority: {case['priority']}")
            print(f"Reason:   {case['reason']}")
            print(f"Evidence: {case['evidence']['scorecard']}")
            print("\nTimeline:")
            for e in case["timeline"]:
                print(f" [{e['timestamp'][:19]}] {e['event'].upper()}: {e['note']}")

        elif args.case_command in ["review", "dismiss"]:
            case = next((c for c in state["cases"] if c["case_id"] == args.case_id), None)
            if not case:
                print(f"[ERROR] Caso {args.case_id} no encontrado.")
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
            print(f"[OK] Caso {case['case_id']} archivado como {case['status']}.")

if __name__ == "__main__":
    main()
