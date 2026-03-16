from __future__ import annotations
import logging
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("bitnin-active-memory-bootstrap")

# Ensure project root is in path
sys.path.append("/home/lucy-ubuntu/Escritorio/NIN")

from verticals.bitnin.services.bitnin_active_memory.extract import MemoryExtractor
from verticals.bitnin.services.bitnin_active_memory.index import ActiveMemoryIndexer

def bootstrap():
    runtime_root = Path("/home/lucy-ubuntu/Escritorio/NIN/verticals/bitnin/runtime")
    
    logger.info("Starting Active Memory Bootstrap...")
    
    try:
        # 1. Extract
        extractor = MemoryExtractor(runtime_root)
        memories = extractor.extract_all()
        logger.info(f"Extracted {len(memories)} memory units from host artifacts.")
        
        if not memories:
            logger.warning("No memories found. Check if artifacts exist in runtime/analyses/normalized/")
            return

        # 2. Index
        indexer = ActiveMemoryIndexer()
        indexer.setup_collection()
        indexer.index_memories(memories)
        
        logger.info("Bootstrap complete. Active Memory is now populated.")
    except Exception as e:
        logger.error(f"Bootstrap failed with error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    bootstrap()
