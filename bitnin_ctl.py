#!/usr/bin/env python3
import argparse
import sys
import json
import subprocess
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

# --- Entrypoint & Path Logic ---
ROOT_DIR = Path(__file__).parent.resolve()
sys.path.append(str(ROOT_DIR))

try:
    from verticals.bitnin.services.bitnin_hitl.hitl_manager import HITLManager
except ImportError:
    print("[CRITICAL] Could not import HITLManager.")
    sys.exit(1)

# Configuration
OBS_DIR = ROOT_DIR / "verticals/bitnin/runtime/observability"
HISTORY_DIR = OBS_DIR / "history"
BUNDLES_DIR = HISTORY_DIR / "daily_bundles"
HEALTH_FILE = HISTORY_DIR / "health_snapshot.json"
STATE_FILE = HISTORY_DIR / "hitl_state.json"

def get_scheduler_status():
    try:
        timer_out = subprocess.check_output(["systemctl", "--user", "status", "bitnin-shadow.timer"], stderr=subprocess.STDOUT, text=True)
        is_active = "active (waiting)" in timer_out or "active (running)" in timer_out
        list_timers = subprocess.check_output(["systemctl", "--user", "list-timers", "bitnin-shadow.timer"], text=True)
        next_run = "Unknown"
        lines = list_timers.splitlines()
        if len(lines) > 1:
            for line in lines:
                if "bitnin-shadow.timer" in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        next_run = f"{parts[0]} {parts[1]}"
        return {"is_timer_active": is_active, "next_run": next_run}
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
    check("Project Root Access", ROOT_DIR.exists())
    check("Runtime Directory Structure", OBS_DIR.exists(), "run ./scripts/bootstrap.sh")
    check("HITL State File present", STATE_FILE.exists())
    check("bitnin_ctl.py executable", os.access(ROOT_DIR / "bitnin_ctl.py", os.X_OK))
    check("bin/bitnin-ctl wrapper present", (ROOT_DIR / "bin/bitnin-ctl").exists())
    sched = get_scheduler_status()
    if "error" not in sched:
        check("BitNin Timer Active", sched["is_timer_active"])
    print("==========================================\n")

def run_weekly_scorecard():
    print("\n=== 📊 BITNIN WEEKLY EXECUTIVE SCORECARD ===")
    today = datetime.now(timezone.utc)
    last_7_days = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
    
    bundles_found = 0
    total_cases_reviewed = 0
    total_briefings = 0
    
    print(f"Period: {last_7_days[-1]} to {last_7_days[0]}")
    print("-" * 40)
    
    for day in reversed(last_7_days):
        day_dir = BUNDLES_DIR / day
        status = "📁" if day_dir.exists() else "⚪"
        if day_dir.exists():
            bundles_found += 1
            # Try to count reviews in journal
            journal = day_dir / "operator_journal.md"
            if journal.exists():
                content = journal.read_text()
                reviews = content.count("EVENT: review") + content.count("EVENT: dismiss")
                total_cases_reviewed += reviews
            total_briefings += 1 if (day_dir / "hitl_briefing.md").exists() else 0
        print(f" [{status}] {day}")

    print("-" * 40)
    print(f"Operational Continuity: {int(bundles_found/7*100)}% (Bundles)")
    print(f"Operator Activity:      {total_cases_reviewed} Decisions recorded")
    
    # Analyze current state
    manager = HITLManager(str(OBS_DIR))
    state = manager.load_state()
    pending = [c for c in state["cases"] if c["status"] == "PENDING"]
    print(f"Current Backlog:        {len(pending)} Pending cases")
    
    verdict = "STABLE" if bundles_found >= 6 and len(pending) < 10 else "WATCH"
    print(f"Weekly Verdict:        {color_status(verdict)}")
    print("============================================\n")

def run_week_review():
    print("\n=== 📅 BITNIN WEEKLY REVIEW PACKET GENERATION ===")
    today = datetime.now(timezone.utc)
    # Using ISO week number for consistent directory naming
    year, week, _ = today.isocalendar()
    yyyy_ww = f"{year}-W{week:02d}"
    week_dir = HISTORY_DIR / "weekly_reviews" / yyyy_ww
    week_dir.mkdir(parents=True, exist_ok=True)
    
    def capture_cmd(args):
        try:
            return subprocess.check_output(args, stderr=subprocess.STDOUT, text=True)
        except subprocess.CalledProcessError as e:
            return e.output
        except Exception as e:
            return str(e)

    ctl_script = ROOT_DIR / "bitnin_ctl.py"
    print(f"Archiving to {week_dir.relative_to(ROOT_DIR)}...")
    
    # 1. weekly_scorecard.md
    scorecard_out = capture_cmd([sys.executable, str(ctl_script), "weekly-scorecard"])
    (week_dir / "weekly_scorecard.md").write_text(f"# Weekly Scorecard\n\n```text\n{scorecard_out}\n```\n")
    
    # 2. system_status.md
    status_out = capture_cmd([sys.executable, str(ctl_script), "status"])
    doctor_out = capture_cmd([sys.executable, str(ctl_script), "doctor"])
    timer_out = capture_cmd(["systemctl", "--user", "status", "bitnin-shadow.timer"])
    timers_out = capture_cmd(["systemctl", "--user", "list-timers", "bitnin-shadow.timer"])
    journal_out = capture_cmd(["journalctl", "--user", "-u", "bitnin-shadow.service", "-n", "50", "--no-pager"])
    
    system_status = f"# System Status\n\n## Status\n```text\n{status_out}\n```\n## Doctor\n```text\n{doctor_out}\n```\n## Timer Status\n```text\n{timer_out}\n```\n## Timers List\n```text\n{timers_out}\n```\n## Journal (Last 50)\n```text\n{journal_out}\n```\n"
    (week_dir / "system_status.md").write_text(system_status)
    
    # 3. hitl_backlog.md
    cases_out = capture_cmd([sys.executable, str(ctl_script), "cases", "list", "--status", "PENDING"])
    if not cases_out.strip():
        cases_out = "No pending cases at snapshot time."
    (week_dir / "hitl_backlog.md").write_text(f"# PENDING HITL Backlog\n\n```text\n{cases_out}\n```\n")
    
    # 4. incident_summary.md
    brief_out = capture_cmd([sys.executable, str(ctl_script), "briefing"])
    (week_dir / "incident_summary.md").write_text(f"# Incident/Briefing Summary\n\n```text\n{brief_out}\n```\n")
    
    # 5. pilot_readiness_week_note.md
    # extracting pending count from manager state directly
    manager = HITLManager(str(OBS_DIR))
    state = manager.load_state()
    pending_count = len([c for c in state.get("cases", []) if c["status"] == "PENDING"])
    
    note_content = f"""# Pilot Readiness - Week Note

**Week:** {yyyy_ww}
**Capture Date:** {today.isoformat()}

## Weekly Decision 
- [ ] `stable`
- [ ] `watch`
- [ ] `investigate`
*(Operator must check one based on the weekly scorecard verdict)*

## Real Incidents this Week
*(See incident_summary.md for the snapshot)*

## Real HITL Backlog
Currently **{pending_count}** pending cases. *(See hitl_backlog.md)*

## Operator Notes
*(Add any qualitative observations here. Do not invent metrics.)*

---
*Reference: [Pilot Readiness Review](../../../../docs/pilot_readiness_review.md)*
"""
    (week_dir / "pilot_readiness_week_note.md").write_text(note_content)
    print(f"[OK] Weekly review packet generated successfully.")

def run_week_close(args):
    ledger_path = HISTORY_DIR / "weekly_review_state.json"
    view_path = HISTORY_DIR / "weekly_review_history.md"
    
    if ledger_path.exists():
        ledger = json.loads(ledger_path.read_text())
    else:
        ledger = {"weeks": []}
        
    week_id = args.week
    existing = next((w for w in ledger["weeks"] if w["week_id"] == week_id), None)
    
    if existing and not args.force:
        print(f"[ERROR] La semana {week_id} ya fue cerrada el {existing['closed_at']}.")
        print("Use --force para sobrescribir la decisión (dejará traza de la corrección).")
        return
        
    week_dir = HISTORY_DIR / "weekly_reviews" / week_id
    if not week_dir.exists():
        print(f"[WARNING] No hay paquete generado para {week_id} (`week-review` no se corrió).")
        
    manager = HITLManager(str(OBS_DIR))
    state = manager.load_state()
    pending_count = len([c for c in state.get("cases", []) if c["status"] == "PENDING"])
    
    now_iso = datetime.now(timezone.utc).isoformat()
    entry = {
        "week_id": week_id,
        "closed_at": now_iso,
        "decision": args.decision,
        "note": args.note,
        "hitl_backlog_at_close": pending_count,
        "incidents_recorded": "See packet",
        "packet_ref": str(week_dir.relative_to(ROOT_DIR)) if week_dir.exists() else "None",
        "is_correction": existing is not None
    }
    
    if existing:
        ledger["weeks"].remove(existing)
        entry["original_decision"] = existing["decision"]
        
    ledger["weeks"].append(entry)
    ledger["weeks"].sort(key=lambda x: x["week_id"])
    
    ledger_path.write_text(json.dumps(ledger, indent=2))
    
    md_lines = [
        "# 🏛️ BitNin Weekly Review Ledger",
        "",
        "Historial canónico de decisiones semanales de gobernanza (Fase 29R).",
        "",
        "| Semana | Decisión | Backlog | Fecha Cierre | Nota Operador | Ref |",
        "|--------|----------|---------|--------------|---------------|-----|"
    ]
    for w in ledger["weeks"]:
        dec_str = "🟢 stable" if w['decision'] == 'stable' else ("🟡 watch" if w['decision'] == 'watch' else "🔴 investigate")
        corr_mark = " *(Corrección)*" if w.get("is_correction") else ""
        md_lines.append(f"| {w['week_id']} | {dec_str} | {w['hitl_backlog_at_close']} | {w['closed_at'][:19]} | {w['note']}{corr_mark} | `{w['packet_ref']}` |")
        
    view_path.write_text("\n".join(md_lines) + "\n")
    
    print(f"\n[OK] Semana {week_id} cerrada con decisión: {args.decision.upper()}")
    print(f"     Ledger guardado en: {ledger_path.relative_to(ROOT_DIR)}")
    print(f"     Vista actualizada:  {view_path.relative_to(ROOT_DIR)}\n")

def main():
    parser = argparse.ArgumentParser(description="BitNin Unified Command Console")
    subparsers = parser.add_subparsers(dest="command", help="Comandos Principales")
    subparsers.add_parser("status", help="Vista 360° de salud y backlog")
    subparsers.add_parser("briefing", help="Resumen ejecutivo diario")
    subparsers.add_parser("day-close", help="Ejecutar ritual de cierre de jornada")
    subparsers.add_parser("doctor", help="Diagnóstico técnico de la instalación")
    subparsers.add_parser("weekly-scorecard", help="Consolidado de gobernanza semanal")
    subparsers.add_parser("week-review", help="Generar el paquete real de revisión semanal S1 (Fase 29R)")

    close_p = subparsers.add_parser("week-close", help="Cerrar formalmente la semana y asentar decisión")
    close_p.add_argument("--week", required=True, help="Semana a cerrar (ej. 2026-W12)")
    close_p.add_argument("--decision", required=True, choices=["stable", "watch", "investigate"], help="Decisión humana final")
    close_p.add_argument("--note", required=True, help="Nota resumen del operador")
    close_p.add_argument("--force", action="store_true", help="Sobrescribir un cierre previo")

    case_parser = subparsers.add_parser("cases", help="Gestión de expedientes HITL")
    case_subparsers = case_parser.add_subparsers(dest="case_command")
    list_p = case_subparsers.add_parser("list", help="Listado de casos")
    list_p.add_argument("--status", choices=["PENDING", "REVIEWED", "DISMISSED", "ESCALATED", "ALL"], default="PENDING")
    show_p = case_subparsers.add_parser("show", help="Inspección de un caso")
    show_p.add_argument("case_id")
    review_p = case_subparsers.add_parser("review", help="Marcar como REVIEWED")
    review_p.add_argument("case_id"); review_p.add_argument("--note", required=True)
    dismiss_p = case_subparsers.add_parser("dismiss", help="Marcar como DISMISSED")
    dismiss_p.add_argument("case_id"); dismiss_p.add_argument("--note", required=True)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    if args.command == "doctor":
        run_doctor()
        return
    
    if args.command == "weekly-scorecard":
        run_weekly_scorecard()
        return
        
    if args.command == "week-review":
        run_week_review()
        return

    if args.command == "week-close":
        run_week_close(args)
        return

    manager = HITLManager(str(OBS_DIR))
    state = manager.load_state()

    if args.command == "status":
        print("\n=== 🎯 BITNIN STATUS 360° ===")
        if HEALTH_FILE.exists():
            health = json.loads(HEALTH_FILE.read_text())
            print(f"System Health: {color_status(health.get('status'))}")
        sched = get_scheduler_status()
        if "error" not in sched:
            icon = "🟢" if sched["is_timer_active"] else "🔴"
            print(f"Scheduler:     {icon} {'Active' if sched['is_timer_active'] else 'Inactive'}")
        cases = state.get("cases", [])
        pending = [c for c in cases if c["status"] == "PENDING"]
        print(f"HITL Backlog:  \033[96m{len(pending)} Pendientes\033[0m")
        print("==============================\n")

    elif args.command == "briefing":
        briefing_file = HISTORY_DIR / "hitl_briefing.md"
        if briefing_file.exists():
            print(briefing_file.read_text())
        else:
            print("[ERROR] Briefing no encontrado.")

    elif args.command == "day-close":
        print("\n--- 🏁 RITUAL DE CIERRE DE JORNADA ---")
        bundle_path = manager.close_day()
        print(f"[OK] Bundle diario generado en: {bundle_path.relative_to(ROOT_DIR)}")

    elif args.command == "cases":
        if not args.case_command:
            case_parser.print_help()
            return
        if args.case_command == "list":
            cases = [c for c in state["cases"] if args.status == "ALL" or c["status"] == args.status]
            for c in sorted(cases, key=lambda x: x["last_updated"], reverse=True)[:10]:
                print(f"{c['case_id']:<20} | {c['status']:<10} | {c['last_updated'][:19]}")
        elif args.case_command == "show":
            case = next((c for c in state["cases"] if c["case_id"] == args.case_id), None)
            if case:
                print(f"\n--- CASE: {case['case_id']} ---\nStatus: {case['status']}\nReason: {case['reason']}")
        elif args.case_command in ["review", "dismiss"]:
            case = next((c for c in state["cases"] if c["case_id"] == args.case_id), None)
            if case:
                case["status"] = "REVIEWED" if args.case_command == "review" else "DISMISSED"
                now = datetime.now(timezone.utc).isoformat()
                case["timeline"].append({"event": args.case_command, "timestamp": now, "note": args.note})
                manager.save_state(state)
                manager.rebuild_views()
                print(f"[OK] {case['case_id']} actualizado.")

if __name__ == "__main__":
    main()
