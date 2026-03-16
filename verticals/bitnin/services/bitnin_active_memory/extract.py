from __future__ import annotations
import json
from pathlib import Path
from typing import List, Dict, Any
import logging

from verticals.bitnin.services.bitnin_active_memory.builder import MemoryBuilder, MemoryUnit

logger = logging.getLogger("bitnin-active-memory-extractor")

class MemoryExtractor:
    def __init__(self, runtime_root: Path):
        self.runtime_root = runtime_root
        self.analyses_dir = runtime_root / "analyses" / "normalized"
        self.records_dir = runtime_root / "execution" / "results"

    def extract_all(self) -> List[MemoryUnit]:
        memories = []
        if not self.analyses_dir.exists():
            logger.warning(f"Analyses directory not found: {self.analyses_dir}")
            return memories
            
        # Scan for normalized analysis files
        analysis_files = list(self.analyses_dir.glob("analysis__*.json"))
        logger.info(f"Scanning {len(analysis_files)} analysis files for memory extraction")
        
        for file_path in analysis_files:
            try:
                analysis = json.loads(file_path.read_text())
                run_id = analysis.get("analysis_id")
                
                # Check for corresponding execution record if possible
                record = None
                if run_id:
                    # We look for a record with the same run_id
                    record_path = self.records_dir / f"{run_id}_record.json"
                    if record_path.exists():
                        record = json.loads(record_path.read_text())
                
                unit = MemoryBuilder.from_artifacts(analysis, record)
                memories.append(unit)
            except Exception as e:
                logger.error(f"Failed to extract memory from {file_path}: {e}")
                
        logger.info(f"Extraction complete. Found {len(memories)} memory units.")
        return memories

if __name__ == "__main__":
    # Quick test
    logging.basicConfig(level=logging.INFO)
    root = Path("/home/lucy-ubuntu/Escritorio/NIN/verticals/bitnin/runtime")
    extractor = MemoryExtractor(root)
    results = extractor.extract_all()
    print(f"Extracted {len(results)} memory units")
