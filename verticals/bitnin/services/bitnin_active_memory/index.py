from __future__ import annotations
import logging
from typing import List, Dict, Any
from verticals.bitnin.services.bitnin_memory_indexer.collections import QdrantCollectionManager
from verticals.bitnin.services.bitnin_memory_indexer.embeddings import OllamaEmbeddingClient
from verticals.bitnin.services.bitnin_active_memory.builder import MemoryUnit

logger = logging.getLogger("bitnin-active-memory-index")

class ActiveMemoryIndexer:
    COLLECTION_NAME = "bitnin_active_memory"
    
    def __init__(self, qdrant: QdrantCollectionManager | None = None, embedder: OllamaEmbeddingClient | None = None):
        self.qdrant = qdrant or QdrantCollectionManager()
        self.embedder = embedder or OllamaEmbeddingClient()

    def setup_collection(self):
        logger.info(f"Ensuring collection {self.COLLECTION_NAME} exists")
        # Dynamic dimension probing
        probe = self.embedder.probe_dimension()
        logger.info(f"Probed dimension: {probe.dimension} using model: {probe.model}")
        self.qdrant.ensure_collection(name=self.COLLECTION_NAME, vector_size=probe.dimension, distance="Cosine")

    def index_memories(self, units: List[MemoryUnit]):
        if not units:
            return
            
        logger.info(f"Indexing {len(units)} units into {self.COLLECTION_NAME}")
        
        texts = []
        payloads = []
        ids = []
        
        for unit in units:
            # We index a semantic summary of the operational situation
            # Enhanced to include outcome and tags for better retrieval context
            tags_str = ",".join(unit.tags)
            text_to_embed = (
                f"{unit.symbol} {unit.interval} {unit.market_summary} "
                f"Action={unit.recommended_action} Status={unit.final_status} "
                f"Outcome={unit.outcome_operativo} Tags=[{tags_str}] "
                f"Confidence={unit.confidence} {unit.narrative_summary}"
            )
            texts.append(text_to_embed)
            payloads.append(unit.to_dict())
            # For simplicity, we use run_id hash or similar as ID if Qdrant needs numeric,
            # but QdrantCollectionManager often handles UUID/strings.
            ids.append(unit.run_id)

        vectors = self.embedder.embed_texts(texts)
        
        # Refactor v3: Using standard REST format for the manager
        import uuid
        points = []
        for i, vector in enumerate(vectors):
            points.append({
                "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, ids[i])),
                "vector": vector,
                "payload": payloads[i]
            })
            
        self.qdrant.upsert_points(
            collection=self.COLLECTION_NAME,
            points=points
        )
        logger.info("Upsert complete")
