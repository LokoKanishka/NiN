"""
NIN Bibliotecario — Human in the Loop
Gestión de pausas, aprobaciones y timeouts para misiones.
"""

import os
import json
import requests
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from . import mission_manager as mm

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
load_dotenv(os.path.join(BASE_DIR, ".env"))

TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID", "0")

# Default timeout: 24 hours
TIMEOUT_HOURS = 24


def send_telegram(text: str) -> bool:
    """Sends a message to Telegram."""
    if not TG_TOKEN:
        print(f"⚠️ [HITL] TG_TOKEN not set, skipping Telegram notification")
        return False
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {
        "chat_id": TG_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        return resp.status_code == 200
    except Exception as e:
        print(f"⚠️ [HITL] Error enviando Telegram: {e}")
        return False


def request_scoping_review(mission_id: str, scope: dict) -> bool:
    """
    Sends a scoping review request to Telegram.
    Pauses the mission at SCOPING state.
    """
    mission = mm.get_mission(mission_id)
    topic = mission.get("topic", "Sin tema")

    # Build a readable scope summary
    scope_text = (
        f"📋 *Revisión de Alcance Requerida*\n\n"
        f"🆔 Misión: `{mission_id}`\n"
        f"📖 Tema: {topic}\n\n"
    )

    if scope.get("topic_refined"):
        scope_text += f"🎯 *Tema refinado:* {scope['topic_refined']}\n\n"

    if scope.get("primary_corpus"):
        scope_text += "📕 *Corpus primario:*\n"
        for item in scope["primary_corpus"][:5]:
            scope_text += f"  • {item}\n"
        scope_text += "\n"

    if scope.get("suggested_focus"):
        scope_text += "🔬 *Enfoques sugeridos:*\n"
        for f in scope["suggested_focus"][:5]:
            scope_text += f"  • {f}\n"
        scope_text += "\n"

    scope_text += (
        f"📊 Máximo de fuentes: {scope.get('max_sources', 25)}\n\n"
        f"👉 Responde:\n"
        f"  `/aprobar {mission_id}` para continuar\n"
        f"  `/rechazar {mission_id}` para ajustar\n"
    )

    mm._log_event(mission_id, "HITL_SCOPING_REVIEW", "Waiting for human approval")
    return send_telegram(scope_text)


def request_corpus_review(mission_id: str, catalog: list[dict]) -> bool:
    """
    Sends a corpus review request to Telegram.
    Pauses the mission at CORPUS_REVIEW state.
    """
    mission = mm.get_mission(mission_id)
    topic = mission.get("topic", "Sin tema")

    primaries = [e for e in catalog if e.get("type") == "primary"]
    secondaries = [e for e in catalog if e.get("type") == "secondary"]

    review_text = (
        f"📚 *Revisión de Corpus Requerida*\n\n"
        f"🆔 Misión: `{mission_id}`\n"
        f"📖 Tema: {topic}\n\n"
        f"📕 Fuentes primarias: {len(primaries)}\n"
    )

    for p in primaries[:5]:
        review_text += f"  • {p.get('author', '?')} — _{p.get('title', '?')}_\n"

    review_text += f"\n📗 Fuentes secundarias: {len(secondaries)}\n"

    for s in secondaries[:5]:
        review_text += f"  • {s.get('author', '?')} — _{s.get('title', '?')}_\n"

    if len(catalog) > 10:
        review_text += f"\n  ... y {len(catalog) - 10} más\n"

    review_text += (
        f"\n👉 Responde:\n"
        f"  `/aprobar {mission_id}` para continuar con curación\n"
        f"  `/rechazar {mission_id}` para ajustar búsqueda\n"
    )

    mm._log_event(mission_id, "HITL_CORPUS_REVIEW", f"{len(catalog)} entries waiting review")
    return send_telegram(review_text)


def notify_mission_event(mission_id: str, event: str, detail: str = "") -> bool:
    """Sends a notification about a mission event to Telegram."""
    icons = {
        "created": "🆕",
        "scoping": "🔬",
        "sourcing": "🔍",
        "corpus_review": "📚",
        "curating": "🧠",
        "dossier": "📋",
        "done": "✅",
        "failed": "❌",
        "hibernated": "💤",
    }
    icon = icons.get(event.lower(), "📌")
    text = f"{icon} *Misión `{mission_id}`*: {event}"
    if detail:
        text += f"\n{detail}"
    return send_telegram(text)


def check_timeout(mission_id: str) -> bool:
    """
    Checks if a mission waiting for review has timed out.
    Returns True if timed out and mission was hibernated.
    """
    mission = mm.get_mission(mission_id)
    if mission["status"] not in ("SCOPING", "CORPUS_REVIEW"):
        return False

    updated = datetime.fromisoformat(mission["updated_at"])
    now = datetime.now(timezone.utc).astimezone()
    elapsed = now - updated

    if elapsed > timedelta(hours=TIMEOUT_HOURS):
        mm.hibernate_mission(mission_id)
        notify_mission_event(
            mission_id, "HIBERNATED",
            f"Sin respuesta por {elapsed.total_seconds() / 3600:.1f}h. "
            f"Misión hibernada. Todo el trabajo queda persistido."
        )
        return True
    return False
