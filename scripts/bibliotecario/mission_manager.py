"""
NIN Bibliotecario — Mission Manager
Gestión de misiones de investigación doctoral con persistencia en disco.
"""

import json
import os
import uuid
from datetime import datetime, timezone

# === PATHS ===
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))  # NIN root
MISSIONS_DIR = os.path.join(BASE_DIR, "runtime", "missions")

# === STATE MACHINE ===
VALID_STATUSES = [
    "QUEUED", "SCOPING", "SOURCING", "CORPUS_REVIEW",
    "CURATING", "DOSSIER", "DONE", "FAILED", "HIBERNATED"
]

VALID_TRANSITIONS = {
    "QUEUED": ["SCOPING", "FAILED", "HIBERNATED"],
    "SCOPING": ["SOURCING", "FAILED", "HIBERNATED"],
    "SOURCING": ["CORPUS_REVIEW", "FAILED", "HIBERNATED"],
    "CORPUS_REVIEW": ["CURATING", "SOURCING", "FAILED", "HIBERNATED"],
    "CURATING": ["DOSSIER", "FAILED", "HIBERNATED"],
    "DOSSIER": ["DONE", "FAILED", "HIBERNATED"],
    "DONE": [],
    "FAILED": [],
    "HIBERNATED": ["QUEUED", "SCOPING", "SOURCING", "CORPUS_REVIEW", "CURATING", "DOSSIER"],
}


def _now_iso() -> str:
    """Returns current timestamp in ISO format with timezone."""
    return datetime.now(timezone.utc).astimezone().isoformat()


def _mission_dir(mission_id: str) -> str:
    """Returns the directory path for a given mission."""
    return os.path.join(MISSIONS_DIR, mission_id)


def _mission_json_path(mission_id: str) -> str:
    """Returns the path to mission.json for a given mission."""
    return os.path.join(_mission_dir(mission_id), "mission.json")


def generate_mission_id() -> str:
    """Generates a unique mission ID with timestamp."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    short_uuid = uuid.uuid4().hex[:6]
    return f"bib_{ts}_{short_uuid}"


def create_mission(
    topic: str,
    source: str = "telegram",
    mission_type: str = "investigacion_doctoral",
    scope: dict = None,
    deliverables: list = None,
) -> dict:
    """
    Creates a new mission and persists it to disk.
    Returns the mission dict.
    """
    mission_id = generate_mission_id()
    mission_path = _mission_dir(mission_id)

    # Create directory structure
    os.makedirs(mission_path, exist_ok=True)
    os.makedirs(os.path.join(mission_path, "notes"), exist_ok=True)

    now = _now_iso()
    mission = {
        "mission_id": mission_id,
        "source": source,
        "type": mission_type,
        "topic": topic,
        "scope": scope or {},
        "deliverables": deliverables or ["catalog", "curation", "dossier"],
        "status": "QUEUED",
        "created_at": now,
        "updated_at": now,
        "artifacts": {
            "catalog": "catalog.json",
            "curation": "curation.json",
            "research_map": "research_map.md",
            "dossier": "dossier.md",
        },
    }

    _save_mission(mission)
    _log_event(mission_id, "CREATED", f"Mission created: {topic}")
    return mission


def _save_mission(mission: dict) -> None:
    """Writes mission dict to mission.json."""
    path = _mission_json_path(mission["mission_id"])
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(mission, f, indent=2, ensure_ascii=False)


def get_mission(mission_id: str) -> dict:
    """Reads a mission from disk. Raises FileNotFoundError if not found."""
    path = _mission_json_path(mission_id)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Mission not found: {mission_id}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def update_status(mission_id: str, new_status: str) -> dict:
    """
    Validates and applies a state transition.
    Returns the updated mission dict.
    Raises ValueError if transition is invalid.
    """
    if new_status not in VALID_STATUSES:
        raise ValueError(f"Invalid status: {new_status}. Valid: {VALID_STATUSES}")

    mission = get_mission(mission_id)
    current = mission["status"]

    if new_status not in VALID_TRANSITIONS.get(current, []):
        raise ValueError(
            f"Invalid transition: {current} → {new_status}. "
            f"Valid from {current}: {VALID_TRANSITIONS[current]}"
        )

    old_status = mission["status"]
    mission["status"] = new_status
    mission["updated_at"] = _now_iso()
    _save_mission(mission)
    _log_event(mission_id, "TRANSITION", f"{old_status} → {new_status}")
    return mission


def update_scope(mission_id: str, scope: dict) -> dict:
    """Updates the scope of a mission."""
    mission = get_mission(mission_id)
    mission["scope"] = scope
    mission["updated_at"] = _now_iso()
    _save_mission(mission)
    _log_event(mission_id, "SCOPE_UPDATED", json.dumps(scope, ensure_ascii=False))
    return mission


def list_missions(status_filter: str = None) -> list:
    """Lists all missions, optionally filtered by status."""
    if not os.path.exists(MISSIONS_DIR):
        return []

    missions = []
    for entry in os.listdir(MISSIONS_DIR):
        mission_path = os.path.join(MISSIONS_DIR, entry, "mission.json")
        if os.path.isfile(mission_path):
            try:
                with open(mission_path, "r", encoding="utf-8") as f:
                    mission = json.load(f)
                if status_filter is None or mission.get("status") == status_filter:
                    missions.append(mission)
            except (json.JSONDecodeError, IOError):
                continue

    # Sort by created_at descending
    missions.sort(key=lambda m: m.get("created_at", ""), reverse=True)
    return missions


def hibernate_mission(mission_id: str) -> dict:
    """Sets a mission to HIBERNATED status, preserving all state."""
    return update_status(mission_id, "HIBERNATED")


def save_artifact(mission_id: str, filename: str, content: str) -> str:
    """Saves an artifact file to the mission directory. Returns the full path."""
    mission_dir = _mission_dir(mission_id)
    os.makedirs(mission_dir, exist_ok=True)
    path = os.path.join(mission_dir, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    _log_event(mission_id, "ARTIFACT_SAVED", filename)
    return path


def save_artifact_json(mission_id: str, filename: str, data: dict | list) -> str:
    """Saves a JSON artifact to the mission directory. Returns the full path."""
    content = json.dumps(data, indent=2, ensure_ascii=False)
    return save_artifact(mission_id, filename, content)


def load_artifact(mission_id: str, filename: str) -> str:
    """Loads a text artifact from the mission directory."""
    path = os.path.join(_mission_dir(mission_id), filename)
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def load_artifact_json(mission_id: str, filename: str) -> dict | list:
    """Loads a JSON artifact from the mission directory."""
    content = load_artifact(mission_id, filename)
    if not content:
        return {}
    return json.loads(content)


def _log_event(mission_id: str, event_type: str, detail: str = "") -> None:
    """Appends an event to the mission log (JSONL)."""
    log_path = os.path.join(_mission_dir(mission_id), "mission_log.jsonl")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    entry = {
        "timestamp": _now_iso(),
        "event": event_type,
        "detail": detail,
    }
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
