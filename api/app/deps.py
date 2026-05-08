from functools import lru_cache
from typing import TYPE_CHECKING

from app.config import settings
from app.retrieval.chroma_store import ChromaStore

if TYPE_CHECKING:
    from app.generation.llm import LLMGenerator


@lru_cache(maxsize=1)
def get_store() -> ChromaStore:
    return ChromaStore(persist_dir=settings.chroma_persist_dir)


@lru_cache(maxsize=1)
def get_generator() -> "LLMGenerator":
    from app.generation.llm import LLMGenerator
    return LLMGenerator()
