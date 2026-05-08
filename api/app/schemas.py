from typing import Literal

from pydantic import BaseModel

SourceType = Literal["primary", "synthesized"]
ContentType = Literal["rule", "philosophy", "research", "general"]


class SourceManifestEntry(BaseModel):
    id: str
    file: str
    title: str
    content_type: ContentType
    audience: list[str]
    age_category: str
    language: str
    url: str
    source_type: SourceType = "primary"


class Chunk(BaseModel):
    chunk_id: str
    source_id: str
    tenant_id: str = "public"
    source_type: SourceType = "primary"
    content_type: ContentType
    audience: list[str]
    age_category: str
    language: str
    url: str
    title: str
    section: str | None = None
    page: int | None = None
    chunk_index: int
    text: str
    contextual_prefix: str | None = None  # filled by Task 9 (Contextual Retrieval)


class QueryRequest(BaseModel):
    question: str
    tenant_id: str = "public"
    top_k: int = 5
    filters: dict[str, str] | None = None


class Citation(BaseModel):
    source_id: str
    title: str
    url: str
    section: str | None = None
    page: int | None = None
    chunk_id: str


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation]
    retrieved_chunks: list[Chunk]
