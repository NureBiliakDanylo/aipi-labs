"""Моделі ембедингів: GeminiEmbedder для роботи через API, HashEmbedder для тестів без мережі, FallbackMiniLMEmbedder."""
import hashlib
import math
import os
import re
from typing import Protocol

class Embedder(Protocol):
    name: str
    dimension: int

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        ...

    def embed_query(self, text: str) -> list[float]:
        ...

def _normalize(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(x * x for x in vector)) or 1.0
    return [x / norm for x in vector]

class HashEmbedder:
    """Детермінований ембедер для тестів без виходу в інтернет."""
    def __init__(self, dimension: int = 384, name: str = "hash-embedder-v1"):
        self.dimension = dimension
        self.name = name

    def _hash_to_vec(self, text: str) -> list[float]:
        words = re.findall(r"\w+", text.lower())
        vec = [0.0] * self.dimension
        if not words:
            return vec
        for w in words:
            h = int(hashlib.md5(w.encode("utf-8")).hexdigest(), 16)
            idx = h % self.dimension
            vec[idx] += 1.0
        return _normalize(vec)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._hash_to_vec(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._hash_to_vec(text)

class GeminiEmbedder:
    """Офіційний клас GeminiEmbedder з різними task_type для документів і запитів (Лістинг 1.9 МВ)."""
    def __init__(self, model: str = "gemini-embedding-001", dim: int = 768, batch_size: int = 50):
        self.model = model
        self.dimension = dim
        self.dim = dim
        self.batch_size = batch_size
        self.name = f"{model}:{dim}"
        self.calls = 0
        self._client = None

    def _get_client(self):
        if self._client is None:
            from google import genai
            self._client = genai.Client()
        return self._client

    def _embed(self, texts: list[str], task: str) -> list[list[float]]:
        from google.genai import types
        vectors: list[list[float]] = []
        client = self._get_client()
        for i in range(0, len(texts), self.batch_size):
            self.calls += 1
            batch = texts[i : i + self.batch_size]
            response = client.models.embed_content(
                model=self.model,
                contents=batch,
                config=types.EmbedContentConfig(
                    task_type=task,
                    output_dimensionality=self.dim,
                ),
            )
            vectors += [_normalize(list(e.values)) for e in response.embeddings]
        return vectors

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._embed(texts, "RETRIEVAL_DOCUMENT")

    def embed_query(self, text: str) -> list[float]:
        return self._embed([text], "RETRIEVAL_QUERY")[0]

class FallbackMiniLMEmbedder:
    """Локальний ембедер all-MiniLM-L6-v2 для порівняння та офлайн роботи."""
    def __init__(self, dimension: int = 384, name: str = "all-MiniLM-L6-v2"):
        self.dimension = dimension
        self.name = name
        self._st = None
        try:
            from sentence_transformers import SentenceTransformer
            self._st = SentenceTransformer(name)
        except Exception:
            self._fallback = HashEmbedder(dimension, name)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if self._st:
            return self._st.encode(texts, normalize_embeddings=True).tolist()
        return self._fallback.embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        if self._st:
            return self._st.encode([text], normalize_embeddings=True)[0].tolist()
        return self._fallback.embed_query(text)
