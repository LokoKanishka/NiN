import json
import logging
import requests
import os
from dotenv import load_dotenv

load_dotenv("/home/lucy-ubuntu/Escritorio/NIN/.env")

# Configuración básica
QDRANT_HOST = "http://127.0.0.1:6335"
COLLECTION_NAME = "nin_knowledge_graph"
VECTOR_SIZE = 1024 # Ajustable según modelo de embeddings

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("GraphMemory")

class GraphMemory:
    def __init__(self):
        self._ensure_collection()

    def _ensure_collection(self):
        try:
            res = requests.get(f"{QDRANT_HOST}/collections/{COLLECTION_NAME}")
            if res.status_code == 404:
                logger.info(f"Creando colección {COLLECTION_NAME}...")
                create_payload = {
                    "vectors": {
                        "size": VECTOR_SIZE,
                        "distance": "Cosine"
                    }
                }
                requests.put(f"{QDRANT_HOST}/collections/{COLLECTION_NAME}", json=create_payload)
                logger.info("Colección creada con éxito.")
            else:
                logger.info(f"Colección {COLLECTION_NAME} detectada.")
        except Exception as e:
            logger.error(f"Error al conectar con Qdrant: {e}")

    def upsert_relation(self, subject, predicate, object_val, metadata=None):
        # En una implementación real de Graph RAG, aquí generaríamos embeddings del "triplete"
        # Por ahora, usaremos un vector dummy o una estructura de puntos para búsqueda de metadatos
        # Para simplificar la demo, guardaremos el texto y metadatos.
        
        point_id = hash(f"{subject}-{predicate}-{object_val}") % (2**63 - 1)
        payload = {
            "subject": subject,
            "predicate": predicate,
            "object": object_val,
            "text": f"{subject} {predicate} {object_val}",
            "metadata": metadata or {}
        }
        
        # Vector dummy (ceros) por ahora, hasta integrar modelo de embeddings real
        vector = [0.0] * VECTOR_SIZE
        
        point = {
            "points": [
                {
                    "id": point_id,
                    "vector": vector,
                    "payload": payload
                }
            ]
        }
        
        try:
            requests.put(f"{QDRANT_HOST}/collections/{COLLECTION_NAME}/points", json=point)
            logger.info(f"Relación guardada: {subject} -> {predicate} -> {object_val}")
            return True
        except Exception as e:
            logger.error(f"Error al guardar relación: {e}")
            return False

    def search_entities(self, query_text, limit=5):
        # Búsqueda por texto en el payload (filtrado)
        # En Qdrant esto se hace vía 'scroll' con filtros o búsqueda vectorial real
        filter_payload = {
            "filter": {
                "must": [
                    {
                        "key": "text",
                        "match": {
                            "text": query_text
                        }
                    }
                ]
            },
            "limit": limit
        }
        
        try:
            res = requests.post(f"{QDRANT_HOST}/collections/{COLLECTION_NAME}/points/scroll", json=filter_payload)
            return res.json().get("result", {}).get("points", [])
        except Exception as e:
            logger.error(f"Error en búsqueda: {e}")
            return []

if __name__ == "__main__":
    gm = GraphMemory()
    gm.upsert_relation("Diego", "autorizo", "Fase 7")
    gm.upsert_relation("NiN-Demon", "escucha", "Telegram")
    print("Test finalizado.")
