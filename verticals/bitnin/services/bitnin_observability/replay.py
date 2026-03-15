from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ReplayManager:
    """Manages historical episode replay and point-in-time analysis."""

    def __init__(self, replay_dir: Path):
        self.replay_dir = replay_dir
        self.replay_dir.mkdir(parents=True, exist_ok=True)

    def register_replay(self, replay_id: str, points: list[dict[str, Any]]) -> Path:
        replay_path = self.replay_dir / f"replay_{replay_id}.json"
        metadata = {
            "replay_id": replay_id,
            "total_points": len(points),
            "points": points
        }
        replay_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return replay_path

    def load_replay(self, replay_id: str) -> dict[str, Any]:
        replay_path = self.replay_dir / f"replay_{replay_id}.json"
        if not replay_path.exists():
            raise FileNotFoundError(f"Replay {replay_id} not found.")
        return json.loads(replay_path.read_text(encoding="utf-8"))
