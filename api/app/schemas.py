from typing import Literal

from pydantic import BaseModel

SourceType = Literal["primary", "synthesized"]
ContentType = Literal["rule", "philosophy", "research", "general"]
# Authority hierarchy — official > semi-official > supplementary.
# Used for retrieval boost and citation badges.
Authority = Literal["official", "semi-official", "supplementary"]
# Coach education level OR practice plan level, where applicable.
# "n/a" for sources that don't fit (e.g. Wikipedia general articles).
Level = Literal["n/a", "Mini", "L1", "L2", "L3", "Rookie", "Starter", "All-Star", "MVP"]
# Chunk-type drives chunker selection AND retrieval semantics.
# - prose: default, recursive splitter (most coaching/research/general content)
# - rule_article: one rule article per chunk (FIBA Rules), keeps art. numbers atomic
# - drill: one drill per chunk (Jr. NBA practice plans), keeps drill atomic
# - chapter: heading-aware chunks for structured manuals
ChunkType = Literal["prose", "rule_article", "drill", "chapter"]


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
    # New for v2 schema — defaults keep older entries valid.
    authority: Authority = "supplementary"
    level: Level = "n/a"
    topic: str | None = None  # e.g. "shooting", "press-break", "spacing", "talent-development"
    region: str = "international"  # international | NL | USA | EU | other
    ruleset: str | None = None  # FIBA | NBA | NCAA | None for non-rule content
    chunk_type: ChunkType = "prose"


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
    contextual_prefix: str | None = None
    # New for v2 — copied from manifest at ingest time.
    authority: Authority = "supplementary"
    level: Level = "n/a"
    topic: str | None = None
    region: str = "international"
    ruleset: str | None = None
    chunk_type: ChunkType = "prose"


class QueryRequest(BaseModel):
    question: str
    tenant_id: str = "public"
    # None -> use the server's tuned default (settings.top_k). Clients may
    # still override per request.
    top_k: int | None = None
    filters: dict[str, str] | None = None


class Citation(BaseModel):
    source_id: str
    title: str
    url: str
    section: str | None = None
    page: int | None = None
    chunk_id: str
    authority: Authority = "supplementary"


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation]
    retrieved_chunks: list[Chunk]
    # True when the answer fell outside the source corpus ("buiten bereik").
    # Drives the frontend's out-of-scope state; computed from the answer text.
    out_of_scope: bool = False
