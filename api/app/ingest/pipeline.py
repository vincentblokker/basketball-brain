import json
import uuid
from collections.abc import Callable
from pathlib import Path

from app.ingest.chunker import recursive_chunk
from app.ingest.page_images import extract_pages
from app.ingest.pdf_loader import load_text
from app.retrieval.chroma_store import ChromaStore
from app.schemas import Chunk, SourceManifestEntry

StageCallback = Callable[[str, int, str], None]
"""Callable signature: (stage, percent, message) -> None.
Stages: loading, chunking, embedding, indexing, done."""


def ingest_corpus(
    raw_dir: Path,
    manifest_path: Path,
    store: ChromaStore,
    chunk_size: int = 800,
    overlap: int = 160,
    use_contextual_retrieval: bool = False,
    on_stage: StageCallback | None = None,
) -> int:
    manifest = [SourceManifestEntry(**e) for e in json.loads(manifest_path.read_text())]
    enricher = None
    if use_contextual_retrieval:
        from app.ingest.contextual import ContextualEnricher
        enricher = ContextualEnricher()

    def emit(stage: str, pct: int, msg: str) -> None:
        if on_stage is not None:
            on_stage(stage, pct, msg)

    total = 0
    for entry in manifest:
        path = raw_dir / entry.file
        if not path.exists():
            print(f"WARN: missing {path}")
            continue

        emit("loading", 25, f"{entry.id}: lezen")
        text = load_text(path)

        # Render PDF pages as PNGs alongside text-extraction.
        # HTML/text sources skip silently. Failure is non-fatal.
        if path.suffix.lower() == ".pdf":
            emit("pages", 30, f"{entry.id}: pagina-thumbnails maken")
            pages_dir = raw_dir.parent / "pages" / entry.id
            page_count = extract_pages(path, pages_dir)
            if page_count:
                print(f"Rendered {page_count} page-images for {entry.id}")

        emit("chunking", 35, f"{entry.id}: chunks maken")
        chunk_texts = recursive_chunk(text, chunk_size=chunk_size, overlap=overlap)

        if enricher is not None:
            prefixes: list[str | None] = list(enricher.enrich_batch(text, chunk_texts))
        else:
            prefixes = [None] * len(chunk_texts)
        chunks = [
            Chunk(
                chunk_id=f"{entry.id}-{i}-{uuid.uuid4().hex[:8]}",
                source_id=entry.id,
                content_type=entry.content_type,
                audience=entry.audience,
                age_category=entry.age_category,
                language=entry.language,
                url=entry.url,
                title=entry.title,
                chunk_index=i,
                text=ct,
                source_type=entry.source_type,
                contextual_prefix=prefixes[i],
                # v2 schema — propagate manifest metadata to each chunk
                authority=entry.authority,
                level=entry.level,
                topic=entry.topic,
                region=entry.region,
                ruleset=entry.ruleset,
                chunk_type=entry.chunk_type,
            )
            for i, ct in enumerate(chunk_texts)
        ]

        n_chunks = len(chunks)
        emit("embedding", 45, f"{entry.id}: embedding 0/{n_chunks}")

        def on_chunk_progress(done: int, total_chunks: int, _entry_id: str = entry.id) -> None:
            # 45→90% range for embedding
            pct = 45 + int(45 * (done / max(total_chunks, 1)))
            emit("embedding", pct, f"{_entry_id}: embedding {done}/{total_chunks}")

        store.add(chunks, on_progress=on_chunk_progress)
        total += n_chunks
        cr_label = " (CR enabled)" if enricher else ""
        print(f"Ingested {n_chunks} chunks from {entry.id}{cr_label}")

    emit("indexing", 95, "afronden")
    return total
