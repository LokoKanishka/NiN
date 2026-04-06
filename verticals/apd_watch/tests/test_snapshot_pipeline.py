import importlib.util
import json
import sys
import unittest
from pathlib import Path

MODULE_PATH = Path("verticals/apd_watch/tools/snapshot_pipeline.py")
SPEC = importlib.util.spec_from_file_location("apd_snapshot_pipeline", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

compute_fingerprint = MODULE.compute_fingerprint
compute_stable_id = MODULE.compute_stable_id
run_pipeline = MODULE.run_pipeline


class SnapshotPipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = Path("verticals/apd_watch/tests/fixtures/apd_offers_sample.json")

    def test_stable_id_is_deterministic(self) -> None:
        a = compute_stable_id("apd_fixture", "MAT-SEC-001", "Profesor/a de Matemática", "La Plata", "Secundaria", "EES N° 12")
        b = compute_stable_id("apd_fixture", "MAT-SEC-001", "profesor/a de matematica", "la plata", "secundaria", "ees n° 12")
        self.assertEqual(a, b)

    def test_fingerprint_changes_with_status_or_closing(self) -> None:
        stable_id = "abc123"
        fp_a = compute_fingerprint(stable_id, "activa", "2026-04-08T21:00:00Z")
        fp_b = compute_fingerprint(stable_id, "anulada", "2026-04-08T21:00:00Z")
        self.assertNotEqual(fp_a, fp_b)

    def test_pipeline_generates_raw_and_normalized(self) -> None:
        # Ejecuta el pipeline en runtime real de la vertical.
        artifacts = run_pipeline(self.fixture, source="apd_fixture", source_snapshot_date="2026-04-06")
        raw = json.loads(Path(artifacts.raw_path).read_text(encoding="utf-8"))
        normalized = json.loads(Path(artifacts.normalized_path).read_text(encoding="utf-8"))

        self.assertEqual(len(raw), 4)
        self.assertEqual(len(normalized), 4)
        self.assertIn("stable_id", normalized[0])
        self.assertIn("fingerprint", normalized[0])
        self.assertTrue(normalized[0]["stable_id"])
        self.assertTrue(normalized[0]["fingerprint"])


if __name__ == "__main__":
    unittest.main()
