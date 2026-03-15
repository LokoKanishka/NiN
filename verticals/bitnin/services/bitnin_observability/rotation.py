from __future__ import annotations

import datetime
from pathlib import Path
from typing import List


class ObservabilityRotator:
    """Helper for managing observability artifacts retention and rotation."""

    def __init__(self, runtime_dir: Path):
        self.runtime_dir = runtime_dir
        self.retention_days = 30  # Default policy

    def list_candidates(self, sub_dir: str, days: int | None = None) -> List[Path]:
        """Lists files older than 'days' in the specified subdirectory."""
        target_days = days or self.retention_days
        target_dir = self.runtime_dir / sub_dir
        if not target_dir.exists():
            return []

        cutoff = datetime.datetime.now() - datetime.timedelta(days=target_days)
        candidates = []
        for item in target_dir.iterdir():
            if item.is_file():
                mtime = datetime.datetime.fromtimestamp(item.stat().st_mtime)
                if mtime < cutoff:
                    candidates.append(item)
        return candidates

    def simulate_rotation(self, sub_dir: str, days: int | None = None):
        """Dry-run rotation log."""
        candidates = self.list_candidates(sub_dir, days)
        print(f"--- Rotation candidates for {sub_dir} ({len(candidates)} files) ---")
        for c in candidates:
            print(f"[DRY-RUN] Would rotate: {c.name}")
        return candidates


if __name__ == "__main__":
    # Example usage for health and logs
    rotator = ObservabilityRotator(Path("/home/lucy-ubuntu/Escritorio/NIN/verticals/bitnin/runtime/observability"))
    rotator.simulate_rotation("health", days=7)
    rotator.simulate_rotation("reports", days=30)
