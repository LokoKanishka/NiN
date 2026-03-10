"""
NIN Bibliotecario — Test Mission
Misión de prueba controlada: "Aristóteles y el motor inmóvil"
Corre el pipeline completo en modo auto-approve y valida los resultados.
"""

import json
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(SCRIPT_DIR))

from bibliotecario import mission_manager as mm
from bibliotecario.pipeline import run_mission


def run_test():
    """Runs the controlled test mission and validates results."""
    
    topic = "Aristóteles y el motor inmóvil: separar primarias y secundarias, proponer líneas de tesis doctoral"
    
    print("=" * 70)
    print("🧪 TEST MISSION: Aristóteles y el motor inmóvil")
    print("=" * 70)
    print()
    
    # Run in auto-approve mode with no Telegram notifications
    mission_id = run_mission(
        topic=topic,
        auto_approve=True,
        notify=False,
        subject_author="Aristóteles",
    )
    
    # === VALIDATION ===
    print("\n" + "=" * 70)
    print("🔍 VALIDACIÓN DE RESULTADOS")
    print("=" * 70)
    
    errors = []
    
    # 1. Mission exists
    try:
        mission = mm.get_mission(mission_id)
        print(f"✅ mission.json existe — ID: {mission_id}")
    except FileNotFoundError:
        errors.append("mission.json no existe")
        print("❌ mission.json no existe")
        return False
    
    # 2. Status is DONE
    if mission.get("status") == "DONE":
        print(f"✅ Estado: DONE")
    else:
        errors.append(f"Estado inesperado: {mission.get('status')}")
        print(f"⚠️ Estado: {mission.get('status')} (esperado: DONE)")
    
    # 3. Catalog exists and has entries
    catalog = mm.load_artifact_json(mission_id, "catalog.json")
    if catalog and isinstance(catalog, list) and len(catalog) > 0:
        primaries = [e for e in catalog if e.get("type") == "primary"]
        secondaries = [e for e in catalog if e.get("type") == "secondary"]
        print(f"✅ catalog.json: {len(catalog)} entradas ({len(primaries)} primarias, {len(secondaries)} secundarias)")
    else:
        errors.append("catalog.json vacío o ausente")
        print(f"⚠️ catalog.json: vacío o ausente")
    
    # 4. Curation exists
    curation = mm.load_artifact_json(mission_id, "curation.json")
    if curation and not curation.get("error"):
        thesis_count = len(curation.get("thesis_lines", []))
        print(f"✅ curation.json: {thesis_count} líneas de tesis")
    else:
        errors.append(f"curation.json con error: {curation.get('error', 'vacío')}")
        print(f"⚠️ curation.json: {curation.get('error', 'vacío o ausente')}")
    
    # 5. Dossier exists
    dossier = mm.load_artifact(mission_id, "dossier.md")
    if dossier and len(dossier) > 100:
        print(f"✅ dossier.md: {len(dossier.splitlines())} líneas")
    else:
        errors.append("dossier.md vacío o ausente")
        print(f"⚠️ dossier.md: vacío o ausente")
    
    # 6. Research map exists
    rmap = mm.load_artifact(mission_id, "research_map.md")
    if rmap and len(rmap) > 50:
        print(f"✅ research_map.md: {len(rmap.splitlines())} líneas")
    else:
        print(f"⚠️ research_map.md: vacío o corto")
    
    # 7. Log exists
    log_path = os.path.join(mm._mission_dir(mission_id), "mission_log.jsonl")
    if os.path.exists(log_path):
        with open(log_path, "r") as f:
            log_lines = f.readlines()
        print(f"✅ mission_log.jsonl: {len(log_lines)} eventos")
    else:
        errors.append("mission_log.jsonl no existe")
        print(f"⚠️ mission_log.jsonl: no existe")
    
    # 8. Directory structure
    mission_dir = mm._mission_dir(mission_id)
    expected_files = ["mission.json", "catalog.json", "curation.json", "dossier.md", "mission_log.jsonl"]
    for f in expected_files:
        if os.path.exists(os.path.join(mission_dir, f)):
            pass  # Already checked above
        else:
            if f not in [e.split()[0] for e in errors]:
                errors.append(f"{f} no existe")
    
    # Summary
    print("\n" + "-" * 40)
    if errors:
        print(f"⚠️ Test completado con {len(errors)} advertencias:")
        for e in errors:
            print(f"   • {e}")
    else:
        print("✅ TEST PASADO: Todos los artefactos generados correctamente.")
    
    print(f"\n📁 Artefactos en: {mission_dir}/")
    print()
    
    return len(errors) == 0


if __name__ == "__main__":
    success = run_test()
    sys.exit(0 if success else 1)
