import json
import uuid
from pathlib import Path

from app.ingest.chunker import recursive_chunk
from app.ingest.pdf_loader import load_text
from app.retrieval.chroma_store import ChromaStore
from app.schemas import Chunk, SourceManifestEntry


def ingest_corpus(
    raw_dir: Path,
    manifest_path: Path,
    store: ChromaStore,
    chunk_size: int = 800,
    overlap: int = 160,
    use_contextual_retrieval: bool = False,
) -> int:
    manifest = [SourceManifestEntry(**e) for e in json.loads(manifest_path.read_text())]
    enricher = None
    if use_contextual_retrieval:
        from app.ingest.contextual import ContextualEnricher
        enricher = ContextualEnricher()

    total = 0
    for entry in manifest:
        path = raw_dir / entry.file
        if not path.exists():
            print(f"WARN: missing {path}")
            continue
        text = load_text(path)
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
            )
            for i, ct in enumerate(chunk_texts)
        ]
        store.add(chunks)
        total += len(chunks)
        cr_label = " (CR enabled)" if enricher else ""
        print(f"Ingested {len(chunks)} chunks from {entry.id}{cr_label}")
    return total
