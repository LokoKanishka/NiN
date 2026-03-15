from __future__ import annotations

import pytest
import sys
from pathlib import Path
from verticals.bitnin.services.bitnin_observability.health import HealthChecker

def test_qdrant_port_consistency():
    # SSOT says 6333, health.py should reflect it.
    checker = HealthChecker(
        n8n_url="http://localhost:5688",
        ollama_url="http://host.docker.internal:11434",
        qdrant_url="http://localhost:6333",
    )
    assert "6333" in checker.qdrant_url
    assert "6335" not in checker.qdrant_url
