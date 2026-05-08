from functools import lru_cache
from typing import TYPE_CHECKING

from app.config import settings
from app.retrieval.chroma_store import ChromaStore

if TYPE_CHECKING:
    from app.generation.llm import LLMGenerator
    from app.retrieval.bm25_index import BM25Index


@lru_cache(maxsize=1)
def get_store() -> ChromaStore:
    return ChromaStore(persist_dir=settings.chroma_persist_dir)


@lru_cache(maxsize=1)
def get_generator() -> "LLMGenerator":
    from app.generation.llm import LLMGenerator
    return LLMGenerator()


@lru_cache(maxsize=1)
def get_bm25() -> "BM25Index":
    """Builds BM25 index from all chunks in the store. Rebuilt at startup."""
    from app.retrieval.bm25_index import BM25Index
    return BM25Index(get_store().all_chunks())
