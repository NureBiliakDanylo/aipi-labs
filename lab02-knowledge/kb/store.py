"""Векторний індекс на Chroma. Ембединги обчислюємо самі й передаємо явно."""
from dataclasses import dataclass
from pathlib import Path
import chromadb
from .chunker import Chunk
from .embedder import Embedder

class EmbedderMismatch(RuntimeError):
    """Колекцію побудовано іншою моделлю ембедингів: потрібна переіндексація."""
    pass

@dataclass
class Hit:
    path: str
    title: str
    heading: str
    text: str
    distance: float

SearchResult = Hit

class KnowledgeStore:
    def __init__(self, *args, **kwargs):
        """
        Універсальна сигнатура, яка підтримує:
        1. KnowledgeStore(embedder, collection="obsidian_kb", path=..., client=...)
        2. KnowledgeStore(client, collection="obsidian_kb", embedder=...)
        3. Будь-які комбінації позиційних та іменованих параметрів.
        """
        client = kwargs.get("client")
        embedder = kwargs.get("embedder")
        collection = kwargs.get("collection")
        path = kwargs.get("path")

        if len(args) >= 1:
            first = args[0]
            if isinstance(first, chromadb.ClientAPI):
                client = first
            else:
                embedder = first
        if len(args) >= 2:
            second = args[1]
            if isinstance(second, str):
                collection = second
            elif isinstance(second, chromadb.ClientAPI):
                client = second
            else:
                embedder = second
        if len(args) >= 3:
            third = args[2]
            if embedder is None:
                embedder = third
            elif client is None and isinstance(third, chromadb.ClientAPI):
                client = third

        self.collection_name = collection or "obsidian_kb"
        self.name = self.collection_name
        self.embedder = embedder

        if client is not None:
            self.client = client
        else:
            p = path or "./chroma_data"
            self.client = chromadb.PersistentClient(path=str(p))

        self.col = self._get_or_create()

    def _get_or_create(self):
        col = self.client.get_or_create_collection(
            name=self.name,
            embedding_function=None,
            configuration={"hnsw": {"space": "cosine"}},
            metadata={"embedder": self.embedder.name, "dim": self.embedder.dimension}
        )
        meta = col.metadata or {}
        if "embedder" in meta and meta["embedder"] != self.embedder.name:
            raise EmbedderMismatch(
                f"collection '{self.name}' was built with {meta['embedder']}, "
                f"current embedder is {self.embedder.name}; rebuild the index"
            )
        return col

    def count(self) -> int:
        return self.col.count()

    def indexed_hashes(self) -> dict[str, str]:
        """{шлях нотатки: хеш вмісту} для інкрементної індексації."""
        data = self.col.get(include=["metadatas"])
        if not data or not data["metadatas"]:
            return {}
        hashes = {}
        for m in data["metadatas"]:
            if "path" in m and "note_hash" in m:
                hashes[m["path"]] = m["note_hash"]
        return hashes

    def add_chunks(self, chunks: list[Chunk], note_hash: str = ""):
        if not chunks:
            return
        embeddings = self.embedder.embed_documents([c.embed_text for c in chunks])
        self.col.upsert(
            ids=[c.id for c in chunks],
            embeddings=embeddings,
            documents=[c.text for c in chunks],
            metadatas=[{
                "path": c.note_path,
                "note_path": c.note_path,
                "title": c.source_link.split("#")[0],
                "heading": c.section,
                "section": c.section,
                "tags": ",".join(c.tags),
                "source_link": c.source_link,
                "note_hash": note_hash,
            } for c in chunks]
        )

    def replace_note(self, chunks: list[Chunk], note_hash: str, tags: list[str]) -> None:
        if chunks:
            self.delete_by_note_path(chunks[0].note_path)
            self.add_chunks(chunks, note_hash=note_hash)

    def delete_by_note_path(self, note_path: str):
        self.col.delete(where={"note_path": note_path})

    def search(self, query: str, top_k: int = 4, tag: str | None = None) -> list[Hit]:
        total = self.count()
        if total == 0:
            return []
        effective_k = min(top_k * 4 if tag else top_k, total)
        q_vec = self.embedder.embed_query(query)
        res = self.col.query(
            query_embeddings=[q_vec],
            n_results=effective_k,
            include=["documents", "metadatas", "distances"]
        )
        hits: list[Hit] = []
        if not res or not res["ids"] or not res["ids"][0]:
            return hits
        for cid, doc, meta, dist in zip(res["ids"][0], res["documents"][0], res["metadatas"][0], res["distances"][0]):
            tags = [t.strip() for t in meta.get("tags", "").split(",") if t.strip()]
            if tag and tag not in tags:
                continue
            hit = Hit(
                path=meta.get("path", meta.get("note_path", "")),
                title=meta.get("title", ""),
                heading=meta.get("heading", meta.get("section", "")),
                text=doc,
                distance=dist
            )
            hit.chunk = Chunk(
                id=cid,
                note_path=meta.get("note_path", ""),
                section=meta.get("section", ""),
                text=doc,
                tags=tags,
                source_link=meta.get("source_link", f"{hit.title}#{hit.heading}")
            )
            hits.append(hit)
            if len(hits) >= top_k:
                break
        return hits
