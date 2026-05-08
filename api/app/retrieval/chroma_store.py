from typing import Any

import chromadb
from chromadb.api.models.Collection import Collection

from app.retrieval.embeddings import Embedder
from app.schemas import Chunk


class ChromaStore:
    """ChromaDB-backed vector + metadata store for chunks.
    Singleton-ish: one collection per (persist_dir, collection_name).
    """

    def __init__(self, persist_dir: str, collection_name: str = "basketball"):
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection: Collection = self.client.get_or_create_collection(
            name=collection_name, metadata={"hnsw:space": "cosine"}
        )
        self.embedder = Embedder()

    def add(self, chunks: list[Chunk]) -> None:
        if not chunks:
            return
        texts = [self._embed_text(c) for c in chunks]
        embeddings = self.embedder.embed(texts).tolist()
        self.collection.add(
            ids=[c.chunk_id for c in chunks],
            embeddings=embeddings,
            documents=[c.text for c in chunks],
            metadatas=[self._metadata(c) for c in chunks],
        )

    def query(
        self,
        question: str,
        top_k: int = 5,
        tenant_id: str = "public",
        filters: dict[str, str] | None = None,
    ) -> list[Chunk]:
        where: dict[str, Any] = {"tenant_id": tenant_id}
        if filters:
            where.update(filters)
        q_emb = self.embedder.embed_query(question).tolist()
        result = self.collection.query(
            query_embeddings=[q_emb],
            n_results=top_k,
            where=where,
        )
        n = len(result["ids"][0]) if result["ids"] else 0
        return [self._chunk_from_query_result(result, i) for i in range(n)]

    def all_chunks(self, tenant_id: str = "public") -> list[Chunk]:
        result = self.collection.get(where={"tenant_id": tenant_id})
        return [
            self._chunk_from_get_result(result, i)
            for i in range(len(result["ids"]))
        ]

    def count(self) -> int:
        return self.collection.count()

    def count_by_source(self, source_id: str, tenant_id: str = "public") -> int:
        result = self.collection.get(
            where={"$and": [{"tenant_id": tenant_id}, {"source_id": source_id}]}
        )
        return len(result["ids"])

    def delete_by_source(self, source_id: str, tenant_id: str = "public") -> int:
        """Delete all chunks for a source. Returns deleted count."""
        result = self.collection.get(
            where={"$and": [{"tenant_id": tenant_id}, {"source_id": source_id}]}
        )
        ids = result["ids"]
        if ids:
            self.collection.delete(ids=ids)
        return len(ids)

    @staticmethod
    def _embed_text(c: Chunk) -> str:
        if c.contextual_prefix:
            return f"{c.contextual_prefix}\n\n{c.text}"
        return c.text

    @staticmethod
    def _metadata(c: Chunk) -> dict[str, Any]:
        return {
            "source_id": c.source_id,
            "tenant_id": c.tenant_id,
            "source_type": c.source_type,
            "content_type": c.content_type,
            "audience": ",".join(c.audience),
            "age_category": c.age_category,
            "language": c.language,
            "url": c.url,
            "title": c.title,
            "section": c.section or "",
            "page": c.page if c.page is not None else -1,
            "chunk_index": c.chunk_index,
            "contextual_prefix": c.contextual_prefix or "",
        }

    @staticmethod
    def _chunk_from_query_result(result: Any, i: int) -> Chunk:
        meta = result["metadatas"][0][i]
        return ChromaStore._chunk_from_meta(
            chunk_id=result["ids"][0][i],
            text=result["documents"][0][i],
            meta=meta,
        )

    @staticmethod
    def _chunk_from_get_result(result: Any, i: int) -> Chunk:
        meta = result["metadatas"][i]
        return ChromaStore._chunk_from_meta(
            chunk_id=result["ids"][i],
            text=result["documents"][i],
            meta=meta,
        )

    @staticmethod
    def _chunk_from_meta(chunk_id: str, text: str, meta: dict[str, Any]) -> Chunk:
        return Chunk(
            chunk_id=chunk_id,
            source_id=meta["source_id"],
            tenant_id=meta["tenant_id"],
            source_type=meta["source_type"],
            content_type=meta["content_type"],
            audience=meta["audience"].split(",") if meta["audience"] else [],
            age_category=meta["age_category"],
            language=meta["language"],
            url=meta["url"],
            title=meta["title"],
            section=meta["section"] or None,
            page=meta["page"] if meta["page"] != -1 else None,
            chunk_index=meta["chunk_index"],
            text=text,
            contextual_prefix=meta["contextual_prefix"] or None,
        )
