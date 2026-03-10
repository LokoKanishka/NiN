"""
NIN Bibliotecario — Telegram Command Handler
Router de comandos Telegram para el Bibliotecario Doctoral.
"""

import os
import json
from dotenv import load_dotenv
from . import mission_manager as mm
from . import hitl

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# Authorized chat IDs
ALLOWED_CHAT_IDS = [int(os.getenv("TG_CHAT_ID", "0"))]


def handle_command(text: str, chat_id: int) -> str:
    """
    Routes a Telegram command to the appropriate handler.
    Returns the response text to send back.
    """
    # Authorization check
    if chat_id not in ALLOWED_CHAT_IDS:
        return "⛔ No autorizado."

    text = text.strip()

    # Route commands
    if text.startswith("/investigar"):
        return cmd_investigar(text)
    elif text.startswith("/estado"):
        return cmd_estado(text)
    elif text.startswith("/misiones"):
        return cmd_misiones()
    elif text.startswith("/aprobar"):
        return cmd_aprobar(text)
    elif text.startswith("/rechazar"):
        return cmd_rechazar(text)
    elif text.startswith("/help") or text.startswith("/start"):
        return cmd_help()
    elif text.startswith("/bibliografia"):
        return cmd_bibliografia(text)
    elif text.startswith("/tesis"):
        return cmd_tesis(text)
    else:
        return (
            "🤔 No reconozco ese comando.\n"
            "Usa /help para ver los comandos disponibles."
        )


def cmd_help() -> str:
    """Returns the help message."""
    return (
        "📚 *NIN Bibliotecario Doctoral*\n\n"
        "Comandos disponibles:\n\n"
        "🔬 `/investigar <tema>` — Inicia una misión de investigación\n"
        "📋 `/estado [mission_id]` — Ver estado de una misión\n"
        "📂 `/misiones` — Listar misiones activas\n"
        "✅ `/aprobar <mission_id>` — Aprobar scope/corpus\n"
        "❌ `/rechazar <mission_id>` — Rechazar y ajustar\n"
        "📚 `/bibliografia <mission_id>` — Ver catálogo\n"
        "🎓 `/tesis <mission_id>` — Ver líneas de tesis\n"
        "❓ `/help` — Este mensaje\n"
    )


def cmd_investigar(text: str) -> str:
    """Creates a new research mission."""
    # Extract topic
    parts = text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        return "⚠️ Uso: `/investigar <tema>`\nEjemplo: `/investigar Aristóteles y el motor inmóvil`"

    topic = parts[1].strip()

    try:
        mission = mm.create_mission(
            topic=topic,
            source="telegram",
            mission_type="investigacion_doctoral",
        )
        mission_id = mission["mission_id"]

        return (
            f"🆕 *Misión creada*\n\n"
            f"🆔 `{mission_id}`\n"
            f"📖 Tema: {topic}\n"
            f"📊 Estado: `QUEUED`\n\n"
            f"El sistema procederá al scoping del tema.\n"
            f"Recibirás una notificación cuando necesite tu aprobación."
        )
    except Exception as e:
        return f"❌ Error creando misión: {e}"


def cmd_estado(text: str) -> str:
    """Shows mission status."""
    parts = text.split(maxsplit=1)

    if len(parts) < 2 or not parts[1].strip():
        # Show latest mission
        missions = mm.list_missions()
        if not missions:
            return "📭 No hay misiones activas."
        mission = missions[0]
    else:
        mission_id = parts[1].strip()
        try:
            mission = mm.get_mission(mission_id)
        except FileNotFoundError:
            return f"❌ Misión no encontrada: `{mission_id}`"

    status_icons = {
        "QUEUED": "⏳", "SCOPING": "🔬", "SOURCING": "🔍",
        "CORPUS_REVIEW": "📚", "CURATING": "🧠", "DOSSIER": "📋",
        "DONE": "✅", "FAILED": "❌", "HIBERNATED": "💤",
    }
    status = mission.get("status", "?")
    icon = status_icons.get(status, "📌")

    return (
        f"{icon} *Estado de Misión*\n\n"
        f"🆔 `{mission['mission_id']}`\n"
        f"📖 Tema: {mission.get('topic', '?')}\n"
        f"📊 Estado: `{status}`\n"
        f"📅 Creada: {mission.get('created_at', '?')}\n"
        f"🔄 Actualizada: {mission.get('updated_at', '?')}\n"
    )


def cmd_misiones() -> str:
    """Lists all active missions."""
    missions = mm.list_missions()
    if not missions:
        return "📭 No hay misiones. Usa `/investigar <tema>` para crear una."

    active = [m for m in missions if m.get("status") not in ("DONE", "FAILED")]
    done = [m for m in missions if m.get("status") in ("DONE", "FAILED")]

    lines = ["📂 *Misiones Activas*\n"]
    for m in active[:10]:
        status = m.get("status", "?")
        lines.append(f"• `{m['mission_id']}` — {m.get('topic', '?')} [{status}]")

    if done:
        lines.append(f"\n📁 Completadas/Fallidas: {len(done)}")

    return "\n".join(lines)


def cmd_aprobar(text: str) -> str:
    """Approves a mission at its current review point."""
    parts = text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        return "⚠️ Uso: `/aprobar <mission_id>`"

    mission_id = parts[1].strip()
    try:
        mission = mm.get_mission(mission_id)
    except FileNotFoundError:
        return f"❌ Misión no encontrada: `{mission_id}`"

    status = mission.get("status")

    if status == "SCOPING":
        mm.update_status(mission_id, "SOURCING")
        return f"✅ Scope aprobado para `{mission_id}`. Iniciando sourcing bibliográfico..."
    elif status == "CORPUS_REVIEW":
        mm.update_status(mission_id, "CURATING")
        return f"✅ Corpus aprobado para `{mission_id}`. Iniciando curación intelectual..."
    else:
        return f"⚠️ La misión `{mission_id}` está en estado `{status}`, no requiere aprobación ahora."


def cmd_rechazar(text: str) -> str:
    """Rejects and adjusts a mission at its current review point."""
    parts = text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        return "⚠️ Uso: `/rechazar <mission_id>`"

    mission_id = parts[1].strip()
    try:
        mission = mm.get_mission(mission_id)
    except FileNotFoundError:
        return f"❌ Misión no encontrada: `{mission_id}`"

    status = mission.get("status")

    if status == "CORPUS_REVIEW":
        mm.update_status(mission_id, "SOURCING")
        return f"🔄 Corpus rechazado para `{mission_id}`. Volviendo a sourcing para ajustes..."
    elif status == "SCOPING":
        mm.update_status(mission_id, "QUEUED")
        return f"🔄 Scope rechazado para `{mission_id}`. Volviendo a cola para replanteamiento..."
    else:
        return f"⚠️ La misión `{mission_id}` está en estado `{status}`, no hay nada que rechazar."


def cmd_bibliografia(text: str) -> str:
    """Shows the bibliography catalog for a mission."""
    parts = text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        return "⚠️ Uso: `/bibliografia <mission_id>`"

    mission_id = parts[1].strip()
    try:
        catalog = mm.load_artifact_json(mission_id, "catalog.json")
    except Exception:
        return f"❌ No se encontró catálogo para `{mission_id}`"

    if not catalog:
        return f"📭 El catálogo de `{mission_id}` está vacío."

    if isinstance(catalog, dict):
        catalog = catalog.get("entries", [])

    primaries = [e for e in catalog if e.get("type") == "primary"]
    secondaries = [e for e in catalog if e.get("type") == "secondary"]

    lines = [f"📚 *Bibliografía de* `{mission_id}`\n"]
    lines.append(f"📕 Primarias: {len(primaries)}")
    for p in primaries[:5]:
        lines.append(f"  • {p.get('author', '?')} — {p.get('title', '?')} ({p.get('year', '?')})")
    lines.append(f"\n📗 Secundarias: {len(secondaries)}")
    for s in secondaries[:5]:
        lines.append(f"  • {s.get('author', '?')} — {s.get('title', '?')} ({s.get('year', '?')})")

    return "\n".join(lines)


def cmd_tesis(text: str) -> str:
    """Shows thesis lines for a mission."""
    parts = text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        return "⚠️ Uso: `/tesis <mission_id>`"

    mission_id = parts[1].strip()
    try:
        curation = mm.load_artifact_json(mission_id, "curation.json")
    except Exception:
        return f"❌ No se encontró curación para `{mission_id}`"

    if not curation or not curation.get("thesis_lines"):
        return f"📭 Aún no hay líneas de tesis para `{mission_id}`."

    lines = [f"🎓 *Líneas de Tesis —* `{mission_id}`\n"]
    for i, th in enumerate(curation["thesis_lines"], 1):
        lines.append(f"*{i}.* {th.get('thesis', '?')}")
        lines.append(f"   _{th.get('justification', '')}_")
        lines.append("")

    return "\n".join(lines)
