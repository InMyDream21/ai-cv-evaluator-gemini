import numpy as np
from typing import List, Tuple
from .llm import embed_text
from .storage import upsert_embedding, get_embeddings_by_namespace
from .config import config

def to_bytes(vector: List[float]) -> bytes:
    return np.asarray(vector, dtype=np.float32).tobytes()

def from_bytes(b: bytes) -> np.ndarray:
    return np.frombuffer(b, dtype=np.float32)

def index_namespace(conn, namespace: str, chunks: List[Tuple[str, str]]):
    """
    texts: List of (chunk_id, text)
    """
    if not chunks:
        return
    vectors = embed_text([text for _, text in chunks])
    for (chunk_id, text), vector in zip(chunks, vectors):
        upsert_embedding(conn, namespace, chunk_id, text, to_bytes(vector))

def top_k(conn, namespace: str, query: str, k: int = 4) -> List[Tuple[str, str, float]]:
    query_vector = embed_text([query])[0]
    query_vector_np = np.array(query_vector, dtype=np.float32)
    embeddings = get_embeddings_by_namespace(conn, namespace)
    results = []
    for chunk_id, text, vector_bytes in embeddings:
        vector_np = from_bytes(vector_bytes)
        if vector_np.shape != query_vector_np.shape:
            continue
        score = np.dot(query_vector_np, vector_np) / (np.linalg.norm(query_vector_np) * np.linalg.norm(vector_np) + 1e-10)
        results.append((chunk_id, text, score))
    results.sort(key=lambda x: x[2], reverse=True)
    return results[:k]