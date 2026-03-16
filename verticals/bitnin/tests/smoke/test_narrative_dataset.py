import os
from pathlib import Path
import pytest

from verticals.bitnin.services.bitnin_analyst.context import CurrentContextBuilder


def test_default_narrative_dataset_resolves():
    """Verify the default narrative path exists and is a non-empty JSONL file."""
    builder = CurrentContextBuilder()
    assert builder.narrative_path.exists(), f"Default narrative dataset not found at {builder.narrative_path}"
    
    # Check it's not empty
    content = builder.narrative_path.read_text(encoding="utf-8")
    lines = [line for line in content.splitlines() if line.strip()]
    assert len(lines) > 0, "Default narrative dataset is empty."
    assert lines[0].startswith("{"), "Default narrative dataset does not appear to be JSONL."


def test_env_override_narrative_dataset(tmp_path):
    """Verify that BITNIN_NARRATIVE_DATASET_PATH overrides the default."""
    dummy_path = tmp_path / "dummy_narrative.jsonl"
    dummy_path.write_text('{"dummy": true}\n', encoding="utf-8")
    
    os.environ["BITNIN_NARRATIVE_DATASET_PATH"] = str(dummy_path)
    try:
        # Reload module to trigger os.getenv again
        import importlib
        from verticals.bitnin.services.bitnin_analyst import context
        importlib.reload(context)
        
        builder = context.CurrentContextBuilder()
        assert builder.narrative_path == dummy_path
    finally:
        del os.environ["BITNIN_NARRATIVE_DATASET_PATH"]


def test_cli_override_narrative_dataset(tmp_path):
    """Verify that passing the path via constructor works (used by CLI)."""
    dummy_path = tmp_path / "dummy_narrative_cli.jsonl"
    dummy_path.write_text('{"dummy": true}\n', encoding="utf-8")
    
    builder = CurrentContextBuilder(narrative_path=dummy_path)
    assert builder.narrative_path == dummy_path
