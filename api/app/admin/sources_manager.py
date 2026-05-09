"""Source CRUD over the manifest file + raw data dir + Chroma."""
import json
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

import httpx

from app.ingest.pipeline import ingest_corpus
from app.retrieval.chroma_store import ChromaStore
from app.schemas import SourceManifestEntry

StageCallback = Callable[[str, int, str], None]


def slugify(text: str) -> str:
    """Lowercase, alphanumerics + hyphens, max 64 chars."""
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:64] or "source"


def _ext_from_url(url: str, content_type: str | None) -> str:
    """Pick a reasonable file extension."""
    ct = (content_type or "").split(";")[0].strip().lower()
    if "pdf" in ct or url.lower().endswith(".pdf"):
        return ".pdf"
    if "html" in ct or url.lower().endswith((".html", ".htm")):
        return ".html"
    if "markdown" in ct or url.lower().endswith(".md"):
        return ".md"
    if "plain" in ct or url.lower().endswith(".txt"):
        return ".txt"
    # default to html for web pages
    return ".html"


class SourcesManager:
    """Manages api/data/raw/sources.json + the raw files alongside it."""

    def __init__(self, raw_dir: Path, store: ChromaStore):
        self.raw_dir = raw_dir
        self.manifest_path = raw_dir / "sources.json"
        self.store = store
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        if not self.manifest_path.exists():
            self.manifest_path.write_text("[]")

    def list_sources(self) -> list[dict[str, Any]]:
        """Return manifest entries enriched with chunk-count from Chroma."""
        manifest = self._read_manifest()
        out: list[dict[str, Any]] = []
        for entry in manifest:
            file_path = self.raw_dir / entry["file"]
            chunk_count = self.store.count_by_source(entry["id"])
            out.append({
                **entry,
                "chunk_count": chunk_count,
                "file_exists": file_path.exists(),
                "file_bytes": file_path.stat().st_size if file_path.exists() else 0,
            })
        return out

    def add_url(
        self,
        url: str,
        title: str,
        content_type: str = "general",
        audience: list[str] | None = None,
        age_category: str = "all",
        language: str = "nl",
        authority: str = "supplementary",
        level: str = "n/a",
        topic: str | None = None,
        region: str = "international",
        ruleset: str | None = None,
        chunk_type: str = "prose",
        on_stage: StageCallback | None = None,
    ) -> dict[str, Any]:
        """Fetch a URL, save the body, register in manifest, ingest. Returns {id, chunk_count}."""
        slug = slugify(title)
        existing_ids = {e["id"] for e in self._read_manifest()}
        idx = 2
        unique_id = slug
        while unique_id in existing_ids:
            unique_id = f"{slug}-{idx}"
            idx += 1

        if on_stage:
            on_stage("fetching", 10, f"URL ophalen: {url[:60]}")

        with httpx.Client(follow_redirects=True, timeout=60.0) as client:
            resp = client.get(
                url,
                headers={"User-Agent": "BasketballBrain/0.1 (+https://brain.clubduty.app)"},
            )
            resp.raise_for_status()
            body = resp.content
            ext = _ext_from_url(url, resp.headers.get("content-type"))

        filename = f"{unique_id}{ext}"
        file_path = self.raw_dir / filename
        file_path.write_bytes(body)

        if on_stage:
            on_stage("saved", 20, f"{len(body):,} bytes opgeslagen")

        entry = {
            "id": unique_id,
            "file": filename,
            "title": title,
            "content_type": content_type,
            "audience": audience or ["all"],
            "age_category": age_category,
            "language": language,
            "url": url,
            "source_type": "primary",
            "authority": authority,
            "level": level,
            "topic": topic,
            "region": region,
            "ruleset": ruleset,
            "chunk_type": chunk_type,
        }
        return self._register_and_ingest(entry, on_stage=on_stage)

    def add_file(
        self,
        filename: str,
        body: bytes,
        title: str,
        content_type: str = "general",
        audience: list[str] | None = None,
        age_category: str = "all",
        language: str = "nl",
        source_url: str = "",
        authority: str = "supplementary",
        level: str = "n/a",
        topic: str | None = None,
        region: str = "international",
        ruleset: str | None = None,
        chunk_type: str = "prose",
        on_stage: StageCallback | None = None,
    ) -> dict[str, Any]:
        """Save uploaded bytes to disk, register, ingest."""
        slug = slugify(title)
        existing_ids = {e["id"] for e in self._read_manifest()}
        idx = 2
        unique_id = slug
        while unique_id in existing_ids:
            unique_id = f"{slug}-{idx}"
            idx += 1

        ext = Path(filename).suffix.lower() or ".bin"
        if ext not in {".pdf", ".html", ".htm", ".md", ".txt"}:
            raise ValueError(f"Unsupported file extension: {ext}")

        target_filename = f"{unique_id}{ext}"
        file_path = self.raw_dir / target_filename
        file_path.write_bytes(body)

        if on_stage:
            on_stage("saved", 20, f"{len(body):,} bytes opgeslagen")

        entry = {
            "id": unique_id,
            "file": target_filename,
            "title": title,
            "content_type": content_type,
            "audience": audience or ["all"],
            "age_category": age_category,
            "language": language,
            "url": source_url or "n/a",
            "source_type": "primary",
            "authority": authority,
            "level": level,
            "topic": topic,
            "region": region,
            "ruleset": ruleset,
            "chunk_type": chunk_type,
        }
        return self._register_and_ingest(entry, on_stage=on_stage)

    def delete_source(self, source_id: str) -> dict[str, Any]:
        """Remove from manifest, delete file, drop chunks from Chroma."""
        manifest = self._read_manifest()
        kept: list[dict[str, Any]] = []
        removed: dict[str, Any] | None = None
        for entry in manifest:
            if entry["id"] == source_id:
                removed = entry
            else:
                kept.append(entry)

        if removed is None:
            raise KeyError(source_id)

        file_path = self.raw_dir / removed["file"]
        if file_path.exists():
            file_path.unlink()

        chunks_deleted = self.store.delete_by_source(source_id)
        self._write_manifest(kept)

        return {"id": source_id, "chunks_deleted": chunks_deleted}

    def reingest(
        self, source_id: str, on_stage: StageCallback | None = None
    ) -> dict[str, Any]:
        """Wipe a source's chunks and re-ingest just that source."""
        manifest = self._read_manifest()
        entry = next((e for e in manifest if e["id"] == source_id), None)
        if entry is None:
            raise KeyError(source_id)

        self.store.delete_by_source(source_id)
        return self._ingest_only(entry, on_stage=on_stage)

    # ---- internals ----

    def _register_and_ingest(
        self, entry: dict[str, Any], on_stage: StageCallback | None = None
    ) -> dict[str, Any]:
        """Append to manifest + ingest. Rolls back on failure — no orphans."""
        manifest = self._read_manifest()
        manifest.append(entry)
        self._write_manifest(manifest)
        try:
            return self._ingest_only(entry, on_stage=on_stage)
        except Exception:
            self._write_manifest([e for e in manifest if e["id"] != entry["id"]])
            file_path = self.raw_dir / entry["file"]
            if file_path.exists():
                file_path.unlink()
            try:
                self.store.delete_by_source(entry["id"])
            except Exception:
                pass  # best-effort
            raise

    def _ingest_only(
        self, entry: dict[str, Any], on_stage: StageCallback | None = None
    ) -> dict[str, Any]:
        tmp_manifest = self.raw_dir / f".manifest-only-{entry['id']}.json"
        tmp_manifest.write_text(json.dumps([entry]))
        try:
            count = ingest_corpus(
                self.raw_dir, tmp_manifest, self.store, on_stage=on_stage
            )
        finally:
            if tmp_manifest.exists():
                tmp_manifest.unlink()
        return {"id": entry["id"], "chunk_count": count}

    def _read_manifest(self) -> list[dict[str, Any]]:
        """Returns manifest entries with v2-schema defaults filled in for
        backward compatibility with v1 entries that lack new fields."""
        if not self.manifest_path.exists():
            return []
        raw = self.manifest_path.read_text()
        if not raw.strip():
            return []
        data: list[dict[str, Any]] = json.loads(raw)
        # Round-trip through the model to pick up defaults for any missing fields.
        return [SourceManifestEntry(**e).model_dump() for e in data]

    def _write_manifest(self, entries: list[dict[str, Any]]) -> None:
        self.manifest_path.write_text(json.dumps(entries, indent=2, ensure_ascii=False))
