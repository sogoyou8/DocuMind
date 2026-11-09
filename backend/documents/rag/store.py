"""Local embedded Chroma index, never an externally exposed Chroma HTTP service."""
import os

from . import COLLECTION_NAME


def collection(client=None):
    if client is None:
        import chromadb
        directory = os.getenv("DOCUMIND_CHROMA_PATH", "/opt/documind-chroma")
        client = chromadb.PersistentClient(path=directory)
    # Real explicit embeddings are supplied by Ollama; no downloading a default
    # model/embedding implementation and no Chroma Cloud communication.
    return client.get_or_create_collection(
        name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"},
    )
