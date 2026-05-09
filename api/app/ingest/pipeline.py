import json
import uuid
from collections.abc import Callable
from pathlib import Path

from app.ingest.chunker import recursive_chunk
from app.ingest.page_images import extract_pages
from app.ingest.pdf_loader import load_pages
from app.retrieval.chroma_store import ChromaStore
from app.schemas import Chunk, SourceManifestEntry

StageCallback = Callable[[str, int, str], None]
"""Callable signature: (stage, percent, message) -> None.
Stages: loading, pages, chunking, embedding, indexing, done."""


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
        # Page-aware loader: list of {page, text}. PDFs get one entry per
        # page; HTML/text get a single entry with page=None.
        pages_data = load_pages(path)

        # Render PDF pages as PNGs alongside text-extraction.
        # HTML/text sources skip silently. Failure is non-fatal.
        if path.suffix.lower() == ".pdf":
            emit("pages", 30, f"{entry.id}: pagina-thumbnails maken")
            pages_dir = raw_dir.parent / "pages" / entry.id
            page_count = extract_pages(path, pages_dir)
            if page_count:
                print(f"Rendered {page_count} page-images for {entry.id}")

        emit("chunking", 35, f"{entry.id}: chunks maken")
        # Chunk per page so each chunk knows its page-number. For non-PDF the
        # single entry is chunked normally and chunks carry page=None.
        chunks: list[Chunk] = []
        chunk_index = 0
        full_text_for_cr = "\n\n".join(p["text"] for p in pages_data)
        for page_entry in pages_data:
            page_text = page_entry["text"]
            page_num = page_entry["page"]
            if not page_text.strip():
                continue
            page_chunk_texts = recursive_chunk(
                page_text, chunk_size=chunk_size, overlap=overlap,
            )
            for ct in page_chunk_texts:
                chunks.append(Chunk(
                    chunk_id=f"{entry.id}-{chunk_index}-{uuid.uuid4().hex[:8]}",
                    source_id=entry.id,
                    content_type=entry.content_type,
                    audience=entry.audience,
                    age_category=entry.age_category,
                    language=entry.language,
                    url=entry.url,
                    title=entry.title,
                    page=page_num,
                    chunk_index=chunk_index,
                    text=ct,
                    source_type=entry.source_type,
                    contextual_prefix=None,  # filled below if CR enabled
                    authority=entry.authority,
                    level=entry.level,
                    topic=entry.topic,
                    region=entry.region,
                    ruleset=entry.ruleset,
                    chunk_type=entry.chunk_type,
                ))
                chunk_index += 1

        # Contextual Retrieval — uses the full document as context (cached)
        # and per-chunk text. Only when enabled.
        if enricher is not None:
            chunk_texts = [c.text for c in chunks]
            prefixes = list(enricher.enrich_batch(full_text_for_cr, chunk_texts))
            for i, prefix in enumerate(prefixes):
                chunks[i].contextual_prefix = prefix

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
