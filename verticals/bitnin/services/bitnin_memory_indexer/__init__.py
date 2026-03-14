"""BitNin memory indexer."""

__all__ = [
    "OllamaEmbeddingClient",
    "QdrantCollectionManager",
    "BitNinMemoryIndexer",
]


def __getattr__(name: str):
    if name == "OllamaEmbeddingClient":
        from .embeddings import OllamaEmbeddingClient

        return OllamaEmbeddingClient
    if name == "QdrantCollectionManager":
        from .collections import QdrantCollectionManager

        return QdrantCollectionManager
    if name == "BitNinMemoryIndexer":
        from .indexer import BitNinMemoryIndexer

        return BitNinMemoryIndexer
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
