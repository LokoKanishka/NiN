from __future__ import annotations
import logging
from typing import Any, Dict, List
from verticals.bitnin.services.bitnin_memory_indexer.collections import QdrantCollectionManager
from verticals.bitnin.services.bitnin_memory_indexer.embeddings import OllamaEmbeddingClient

logger = logging.getLogger("bitnin-active-memory-retriever")

class ActiveMemoryRetriever:
    COLLECTION_NAME = "bitnin_active_memory"
    
    def __init__(self, qdrant: QdrantCollectionManager | None = None, embedder: OllamaEmbeddingClient | None = None):
        self.qdrant = qdrant or QdrantCollectionManager()
        self.embedder = embedder or OllamaEmbeddingClient()

    def retrieve(self, context: Dict[str, Any], top_k: int = 5) -> List[Dict[str, Any]]:
        market = context.get("market_state", {})
        narrative = context.get("recent_narrative", {})
        
        # Build query string matching the indexing format
        market_summary = market.get('summary', '')
        topics_str = "|".join(narrative.get('top_topics', []))
        query_text = (
            f"{market.get('symbol')} {market.get('interval')} "
            f"{market_summary} "
            f"topics={topics_str}"
        )
        
        logger.info(f"Retrieving active memory with query: {query_text}")
        
        vector = self.embedder.embed_texts([query_text])[0]
        
        # Simple search using the manager
        results = self.qdrant.search(
            collection=self.COLLECTION_NAME,
            vector=vector,
            limit=top_k
        )
        
        # Normalize results for the analyst
        normalized = []
        for item in results:
            payload = item.get("payload", {})
            normalized.append({
                "run_id": payload.get("run_id"),
                "timestamp": payload.get("timestamp"),
                "action": payload.get("recommended_action"),
                "status": payload.get("final_status"),
                "outcome": payload.get("outcome_operativo"),
                "tags": payload.get("tags", []),
                "confidence": payload.get("confidence"),
                "reasoning": payload.get("notes", [payload.get("narrative_summary", "")])[0],
                "score": round(float(item.get("score", 0.0)), 4)
            })
            
        return normalized
